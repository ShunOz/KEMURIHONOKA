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


def test_summary_strips_tags_and_truncates():
    s = content.build_summary("本日も営業 #煙仄 @x", "煙仄", "https://ig/1")
    assert "#" not in s and "@" not in s and "https://ig/1" in s
    assert len(content.build_summary("あ" * 3000, "煙仄", "")) <= 1500
    assert "最新情報" in content.build_summary("#only", "煙仄", "")
