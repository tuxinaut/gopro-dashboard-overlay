import inspect
import os
from pathlib import Path

from gopro_overlay import ffmpeg, timeseries_process
from gopro_overlay.framemeta import gps_framemeta, FrameMeta
from gopro_overlay.gpmd import GoproMeta
from gopro_overlay.gpmd_calculate import timestamp_calculator_for_packet_type
from gopro_overlay.gpmd_visitors_xyz import XYZVisitor, XYZComponentConverter
from gopro_overlay.units import units


def load_file(path) -> GoproMeta:
    return GoproMeta.parse(ffmpeg.load_gpmd_from(path))


def file_path_of_test_asset(name):
    sourcefile = Path(inspect.getfile(file_path_of_test_asset))

    meta_dir = sourcefile.parents[0].joinpath("meta")

    the_path = os.path.join(meta_dir, name)

    if not os.path.exists(the_path):
        raise IOError(f"Test file {the_path} does not exist")

    return the_path


def test_loading_data_by_frame():
    filepath = file_path_of_test_asset("hero7.mp4")
    meta = load_file(filepath)

    metameta = ffmpeg.find_streams(filepath).meta

    gps_framemeta(
        meta,
        metameta=metameta,
        units=units
    )


def accl_framemeta(meta, units, metameta=None):
    framemeta = FrameMeta()

    meta.accept(
        XYZVisitor(
            "ACCL",
            XYZComponentConverter(
                frame_calculator=timestamp_calculator_for_packet_type(meta, metameta, "ACCL"),
                units=units,
                on_item=lambda t, x: framemeta.add(t, x)
            ).convert
        )
    )

    kalman = timeseries_process.process_kalman_pp3("accl", lambda i: i.accel)
    framemeta.process(kalman)

    return framemeta


def test_loading_accl():
    filepath = "/home/richja/dev/gopro-graphics/render/test-rotating-slowly.MP4"
    meta = load_file(filepath)
    stream_info = ffmpeg.find_streams(filepath)

    framemeta = accl_framemeta(meta, units, stream_info.meta)

    item = framemeta.items()[0]
    assert f"{item.accl.x.units:P~}" == "m/s²"
    assert f"{item.accl.y.units:P~}" == "m/s²"
    assert f"{item.accl.z.units:P~}" == "m/s²"


