The Jenkins hash functions are a family of non-cryptographic hash functions for multi-byte keys designed by Bob Jenkins. The first one was formally published in 1997.

The hash functions
one_at_a_time
Jenkins's one_at_a_time (joaat) hash is adapted here from a WWW page by Bob Jenkins,[1] which is an expanded version of his Dr. Dobb's article.[2] It was originally created to fulfill certain requirements described by Colin Plumb, a cryptographer.[1] Rockstar Games' RAGE engine makes extensive use of this hashing function.[3]

uint32_t jenkins_one_at_a_time_hash(const uint8_t* key, size_t length) {
  size_t i = 0;
  uint32_t hash = 0;
  while (i != length) {
    hash += key[i++];
    hash += hash << 10;
    hash ^= hash >> 6;
  }
  hash += hash << 3;
  hash ^= hash >> 11;
  hash += hash << 15;
  return hash;
}
Sample hash values for one_at_a_time hash function.

one_at_a_time("a", 1)
0xca2e9442
one_at_a_time("The quick brown fox jumps over the lazy dog", 43)
0x519e91f5

Avalanche behavior of Jenkins One-at-a-time hash over 3-byte keys
The avalanche behavior of this hash is shown on the right.

Each of the 24 rows corresponds to a single bit in the 3-byte input key, and each of the 32 columns corresponds to a bit in the output hash. Colors are chosen by how well the input key bit affects the given output hash bit: a green square indicates good mixing behavior, a yellow square weak mixing behavior, and red would indicate no mixing. Only a few bits in the last byte of the input key are weakly mixed to a minority of bits in the output hash.

Standard implementations of the Perl programming language prior to version 5.28 included Jenkins's one-at-a-time hash or a hardened variant of it, which was used by default.