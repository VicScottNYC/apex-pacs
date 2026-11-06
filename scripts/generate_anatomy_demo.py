from hashlib import sha256
from pathlib import Path

from PIL import Image
from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "fixtures" / "synthetic-abdomen.png"
OUTPUT = ROOT / "samples" / "apex-anatomy-demo.dcm"


def main():
    digest = sha256(SOURCE.read_bytes()).hexdigest()
    study_uid, series_uid, instance_uid = (
        generate_uid(entropy_srcs=["APEX-ANATOMY-v2", digest, kind])
        for kind in ("study", "series", "instance")
    )
    meta = FileMetaDataset()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = instance_uid
    image = FileDataset(str(OUTPUT), {}, file_meta=meta, preamble=b"\0" * 128)
    image.SOPClassUID = meta.MediaStorageSOPClassUID
    image.SOPInstanceUID = instance_uid
    image.StudyInstanceUID = study_uid
    image.SeriesInstanceUID = series_uid
    image.PatientName = "Synthetic^Anatomy"
    image.PatientID = "APEX-ANATOMY-001"
    image.PatientBirthDate = image.PatientSex = ""
    image.StudyDate = "20260101"
    image.StudyTime = "120000"
    image.StudyID = "ANATOMY001"
    image.AccessionNumber = image.ReferringPhysicianName = ""
    image.StudyDescription = "Synthetic Abdomen - Axial Demo"
    image.SeriesDescription = "Synthetic axial anatomy illustration"
    image.ImageType = ["DERIVED", "SECONDARY"]
    image.Modality = "OT"
    image.ConversionType = "SYN"
    image.SeriesNumber = image.InstanceNumber = 1
    image.BurnedInAnnotation = "NO"
    image.SamplesPerPixel = 1
    image.PhotometricInterpretation = "MONOCHROME2"
    image.BitsAllocated = image.BitsStored = 8
    image.HighBit = 7
    image.PixelRepresentation = 0
    image.WindowCenter = 128
    image.WindowWidth = 256
    with Image.open(SOURCE) as source:
        grayscale = source.convert("L")
        image.Columns, image.Rows = grayscale.size
        pixels = grayscale.tobytes()
    image.PixelData = pixels + (b"\0" if len(pixels) % 2 else b"")
    OUTPUT.parent.mkdir(exist_ok=True)
    image.save_as(OUTPUT, enforce_file_format=True)
    print(study_uid)


if __name__ == "__main__":
    main()
