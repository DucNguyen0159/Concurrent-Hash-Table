//! Jenkins one-at-a-time hash (Bob Jenkins), `uint32_t` semantics.

/// Jenkins one-at-a-time hash over UTF-8 bytes (ASCII names in test data).
pub fn jenkins_one_at_a_time(key: &str) -> u32 {
    let mut hash: u32 = 0;
    for byte in key.as_bytes() {
        hash = hash.wrapping_add(*byte as u32);
        hash = hash.wrapping_add(hash << 10);
        hash ^= hash >> 6;
    }
    hash = hash.wrapping_add(hash << 3);
    hash ^= hash >> 11;
    hash = hash.wrapping_add(hash << 15);
    hash
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn jenkins_one_byte_a() {
        assert_eq!(jenkins_one_at_a_time("a"), 0xCA2E9442);
    }

    /// Matches `PA#2 Expected Output.md` / course workload (differs from some older sample logs).
    #[test]
    fn jenkins_shigeru_matches_expected_output_doc() {
        assert_eq!(jenkins_one_at_a_time("Shigeru Miyamoto"), 1_874_280_167);
    }
}
