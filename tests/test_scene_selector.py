from video.scene_selector import SceneSelector


def test_keyword_match():
    assets = ["https://img.example.com/ao_red.jpg", "https://img.example.com/ao_blue.jpg"]
    sentences = ["Màu đỏ rực rỡ", "Phối đồ với xanh dương"]
    s = SceneSelector()
    pairs = s.match(assets, sentences)
    assert pairs[0][1] == assets[0]
    assert pairs[1][1] == assets[1]


def test_fallback_round_robin():
    assets = ["img1.jpg"]
    sentences = ["a", "b", "c"]
    s = SceneSelector()
    pairs = s.match(assets, sentences)
    assert all(p[1] == "img1.jpg" for p in pairs)


def test_distribute_assets_when_keywords_overlap():
    assets = ["a.jpg", "b.jpg"]
    # Both sentences mention 'ao' so keyword scoring may prefer same asset, but we expect distribution
    sentences = ["ao dep", "ao chat", "ao xuat", "ao moi"]
    s = SceneSelector()
    pairs = s.match(assets, sentences)
    assigned = [p[1] for p in pairs]
    # ensure we used both assets before reusing
    assert set(assigned[:2]) == set(assets)


def test_no_immediate_repeat_until_all_used():
    assets = [f"img{i}.jpg" for i in range(3)]
    sentences = [f"s{i}" for i in range(6)]
    s = SceneSelector()
    pairs = s.match(assets, sentences)
    for i in range(0, 6, 3):
        window = [p[1] for p in pairs[i:i+3]]
        assert len(set(window)) == 3  # all assets used once per window
