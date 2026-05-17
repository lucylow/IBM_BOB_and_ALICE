"""Improved Cascade error correction and privacy amplification."""
import random
import hashlib
from typing import List, Tuple

def cascade_correct(alice_key: List[int], bob_key: List[int], block_size: int = 64, max_passes: int = 3) -> Tuple[List[int], List[int], int]:
    """
    Cascade error correction protocol.
    Returns corrected keys (now identical) and number of parity bits revealed.
    """
    if not isinstance(alice_key, list) or not all(isinstance(x, int) for x in alice_key):
        raise TypeError("alice_key must be a list of integers.")
    if not isinstance(bob_key, list) or not all(isinstance(x, int) for x in bob_key):
        raise TypeError("bob_key must be a list of integers.")
    if len(alice_key) != len(bob_key):
        raise ValueError("alice_key and bob_key must have the same length.")
    if not isinstance(block_size, int) or block_size <= 0:
        raise ValueError("block_size must be a positive integer.")
    if not isinstance(max_passes, int) or max_passes <= 0:
        raise ValueError("max_passes must be a positive integer.")

    n = len(alice_key)
    if n == 0:
        return [], [], 0

    alice = alice_key[:]
    bob = bob_key[:]
    total_parities = 0

    for pass_num in range(max_passes):
        # Shuffle indices together
        indices = list(range(n))
        random.shuffle(indices)
        
        # Create shuffled copies for this pass
        alice_shuffled = [alice[i] for i in indices]
        bob_shuffled = [bob[i] for i in indices]

        # Process in blocks
        for start in range(0, n, block_size):
            end = min(start + block_size, n)
            
            # Calculate parity for the current block
            alice_parity = sum(alice_shuffled[start:end]) % 2
            bob_parity = sum(bob_shuffled[start:end]) % 2
            total_parities += 1

            if alice_parity != bob_parity:
                # Binary search inside block to find the error
                lo, hi = start, end - 1
                while lo < hi:
                    mid = (lo + hi) // 2
                    # Parity of the left half of the current search range
                    a_par = sum(alice_shuffled[start:mid+1]) % 2
                    b_par = sum(bob_shuffled[start:mid+1]) % 2
                    total_parities += 1
                    if a_par != b_par:
                        hi = mid
                    else:
                        lo = mid + 1
                # Flip the bit at position `lo` in Bob's shuffled key
                bob_shuffled[lo] ^= 1
        
        # Unshuffle the keys to their original order for the next pass or final output
        # This step is crucial to ensure that the keys are correctly aligned for subsequent passes
        # or for privacy amplification.
        current_alice = [0] * n
        current_bob = [0] * n
        for original_idx, shuffled_idx in enumerate(indices):
            current_alice[shuffled_idx] = alice_shuffled[original_idx]
            current_bob[shuffled_idx] = bob_shuffled[original_idx]
        alice = current_alice
        bob = current_bob

    return alice, bob, total_parities

def privacy_amplification(key: List[int], reduction_factor: float = 0.5) -> List[int]:
    """
    Use random hashing (SHA256) to compress the key.
    """
    if not isinstance(key, list) or not all(isinstance(x, int) for x in key):
        raise TypeError("key must be a list of integers.")
    if not isinstance(reduction_factor, (int, float)) or not (0.0 < reduction_factor <= 1.0):
        raise ValueError("reduction_factor must be a float between 0.0 and 1.0.")

    if not key:
        return []

    key_str = ".".join(str(b) for b in key) # Use a separator to avoid ambiguity with concatenated bits
    
    # Calculate target hash length. Ensure it's at least 1 if key is not empty.
    target_hash_len = max(1, int(len(key) * reduction_factor))

    # Use SHA256 and truncate to the target_hash_len bits
    hashed_bytes = hashlib.sha256(key_str.encode("utf-8")).digest()
    
    bits = []
    for byte in hashed_bytes:
        for i in range(8):
            bits.append((byte >> (7 - i)) & 1) # Read bits from MSB to LSB
            if len(bits) == target_hash_len:
                return bits
    return bits[:target_hash_len]
