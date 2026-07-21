import os

import libtorrent as lt

import config

_session: lt.session | None = None


def get_session() -> lt.session:
    global _session
    if _session is None:
        _session = lt.session()
        _session.listen_on(config.SEED_PORT_MIN, config.SEED_PORT_MAX)
    return _session


def create_torrent_and_seed(file_path: str):
    """
    Hashes the local file, writes a .torrent, builds a magnet link,
    and starts seeding it in-process so peers can pull it P2P.
    Returns (magnet_uri, info_hash, torrent_path)
    """
    fs = lt.file_storage()
    lt.add_files(fs, file_path)
    t = lt.create_torrent(fs)

    for tr in config.TRACKERS:
        t.add_tracker(tr)
    t.set_creator("TeleBinBot")

    lt.set_piece_hashes(t, os.path.dirname(file_path))
    torrent_data = lt.bencode(t.generate())

    os.makedirs(config.TORRENT_DIR, exist_ok=True)
    torrent_path = os.path.join(
        config.TORRENT_DIR, os.path.basename(file_path) + ".torrent"
    )
    with open(torrent_path, "wb") as f:
        f.write(torrent_data)

    info = lt.torrent_info(torrent_path)
    info_hash = str(info.info_hash())
    magnet = lt.make_magnet_uri(info)

    ses = get_session()
    handle = ses.add_torrent(
        {
            "ti": info,
            "save_path": os.path.dirname(file_path),
            "seed_mode": True,
        }
    )
    handle.set_upload_limit(0)  # unlimited

    return magnet, info_hash, torrent_path
