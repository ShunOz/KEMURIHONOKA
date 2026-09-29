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


LOC = {"name": "煙仄 新宿店", "seo": {"area": "新宿", "category": "燻製バー",
       "nearby": "新宿駅東口から徒歩3分", "keywords": ["新宿 燻製"]}}


def test_template_has_name_area_and_no_url_or_tags():
    s = content.build_summary("本日も営業 #煙仄 @x https://ig/1", LOC)
    assert s.startswith("煙仄 新宿店（新宿燻製バー）")
    assert "#" not in s and "@" not in s and "http" not in s
    assert not content.validate(s, LOC)


def test_validate_catches_problems():
    bad = "電話 03-1234-5678 https://x.jp #tag!!" + "新宿 燻製" * 3
    p = " ".join(content.validate(bad, LOC))
    for w in ["URL", "電話", "ハッシュタグ", "感嘆符", "店名", "キーワード過多"]:
        assert w in p


def test_truncates_and_empty_caption():
    assert len(content.build_summary("あ" * 3000, LOC)) <= 1500
    assert "煙仄 新宿店" in content.build_summary("#only", LOC)
