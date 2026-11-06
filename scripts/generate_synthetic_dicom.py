from pathlib import Path

from pydicom.dataset import FileDataset, FileMetaDataset
from pydicom.uid import ExplicitVRLittleEndian, SecondaryCaptureImageStorage, generate_uid


def main():
    output = Path("samples/apex-rebuild-sc.dcm")
    output.parent.mkdir(parents=True, exist_ok=True)

    meta = FileMetaDataset()
    meta.TransferSyntaxUID = ExplicitVRLittleEndian
    meta.MediaStorageSOPClassUID = SecondaryCaptureImageStorage
    meta.MediaStorageSOPInstanceUID = generate_uid()

    image = FileDataset(str(output), {}, file_meta=meta, preamble=b"\0" * 128)
    image.SOPClassUID = meta.MediaStorageSOPClassUID
    image.SOPInstanceUID = meta.MediaStorageSOPInstanceUID
    image.StudyInstanceUID = generate_uid()
    image.SeriesInstanceUID = generate_uid()
    image.PatientName = "Synthetic^Apex"
    image.PatientID = "APEX-REBUILD-001"
    image.PatientBirthDate = ""
    image.PatientSex = ""
    image.StudyDate = "20260101"
    image.StudyTime = "120000"
    image.StudyID = "REBUILD001"
    image.AccessionNumber = ""
    image.ReferringPhysicianName = ""
    image.StudyDescription = "APEX Synthetic Rebuild"
    image.Modality = "OT"
    image.ConversionType = "SYN"
    image.SeriesNumber = 1
    image.InstanceNumber = 1
    image.BurnedInAnnotation = "NO"
    image.Rows = image.Columns = 128
    image.SamplesPerPixel = 1
    image.PhotometricInterpretation = "MONOCHROME2"
    image.BitsAllocated = image.BitsStored = 8
    image.HighBit = 7
    image.PixelRepresentation = 0
    image.PixelData = bytes(
        230 if (x - 64) ** 2 + (y - 64) ** 2 < 32 ** 2 else 2 * x
        for y in range(image.Rows)
        for x in range(image.Columns)
    )
    image.save_as(output, enforce_file_format=True, overwrite=False)
    print(f"Created {output}")


if __name__ == "__main__":
    main()
