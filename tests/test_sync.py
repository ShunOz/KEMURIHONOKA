from datetime import datetime, timedelta, timezone

from gbp_sync import content, instagram
from gbp_sync.main import select_new


def item(id, days_ago, mtype="IMAGE", children=None):
    ts = (datetime.now(timezone.utc) - timedelta(days=days_ago)).strftime("%Y-%m-%dT%H:%M:%S+0000")
    d = {"id": id, "caption": "本日も営業 #煙仄 @x", "media_type": mtype,
         "media_url": f"https://cdn/{id}", "permalink": f"https://ig/{id}", "timestamp": ts}
    if children:
        d["children"] = {"data": children}
    return d


def test_parse_carousel_and_video():
    m = instagram.parse_media(item("a", 1, "CAROUSEL_ALBUM", [
        {"id": "c1", "media_type": "IMAGE", "media_url": "u1"},
        {"id": "c2", "media_type": "VIDEO", "media_url": "u2"}]))
    assert m.assets == [("PHOTO", "u1"), ("VIDEO", "u2")]


def test_select_new_filters_old_and_done():
    ms = [instagram.parse_media(item(i, d)) for i, d in [("new", 1), ("old", 30), ("done", 2)]]
    got = select_new(ms, {"done"}, 14, 5)
    assert [m.id for m in got] == ["new"]


LOC = {"name": "煙仄 新宿本店", "seo": {"area": "新宿", "category": "燻製バー",
       "nearby": "新宿駅東口から徒歩3分", "keywords": ["新宿 燻製"]}}


def test_template_has_name_area_and_no_url_or_tags():
    s = content.build_summary("本日も営業 #煙仄 @x https://ig/1", LOC)
    assert s.startswith("煙仄 新宿本店（新宿燻製バー）")
    assert "#" not in s and "@" not in s and "http" not in s
    assert not content.validate(s, LOC)


def test_validate_catches_problems():
    bad = "電話 03-1234-5678 https://x.jp #tag!!" + "新宿 燻製" * 3
    p = " ".join(content.validate(bad, LOC))
    for w in ["URL", "電話", "ハッシュタグ", "感嘆符", "店名", "キーワード過多"]:
        assert w in p


def test_truncates_and_empty_caption():
    assert len(content.build_summary("あ" * 3000, LOC)) <= 1500
    assert "煙仄 新宿本店" in content.build_summary("#only", LOC)


def test_handoff_prepare_and_issue_body(tmp_path, monkeypatch):
    from gbp_sync import handoff

    class R:
        content = b"data"
        def raise_for_status(self): pass

    monkeypatch.setattr(handoff.requests, "get", lambda *a, **k: R())
    m = instagram.parse_media(item("a1", 1, "CAROUSEL_ALBUM", [
        {"id": "c1", "media_type": "IMAGE", "media_url": "u1"},
        {"id": "c2", "media_type": "VIDEO", "media_url": "u2"}]))
    loc = {"key": "shinjuku", "name": "煙仄 新宿本店"}
    d = handoff.prepare(m, "本文", loc, tmp_path)
    assert sorted(p.name for p in d.iterdir()) == ["01_photo.jpg", "02_video.mp4", "post.txt"]
    body = handoff.issue_body(m, "本文", loc, "https://run")
    assert "本文" in body and "写真 1 枚 / 動画 1 本" in body and m.permalink in body


def test_create_issue_requires_token(monkeypatch):
    import pytest
    from gbp_sync import handoff
    monkeypatch.delenv("GITHUB_TOKEN", raising=False)
    m = instagram.parse_media(item("a", 1))
    with pytest.raises(RuntimeError):
        handoff.create_issue(m, "x", {"name": "n", "key": "k"})


def test_manual_mode_does_not_need_gbp_location(monkeypatch):
    from gbp_sync import main as m
    monkeypatch.setenv("T", "tok")
    seen = {}
    monkeypatch.setattr(m.instagram, "fetch_recent", lambda *a: seen.setdefault("called", []) or [])
    loc = {"key": "k", "name": "n", "ig_user_id": "1", "gbp_location": "", "ig_token_env": "T"}
    cfg = {"lookback_posts": 1, "max_age_days": 1, "max_posts_per_run": 1, "rewrite_with_claude": False}
    m.process(loc, cfg, set(), None, "", "manual")
    assert "called" in seen                      # スキップされず取得まで進む
    seen.clear()
    m.process(loc, cfg, set(), None, "", "api")
    assert "called" not in seen                  # apiモードでは未設定でスキップ
