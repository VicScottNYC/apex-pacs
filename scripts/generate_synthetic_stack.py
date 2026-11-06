from pathlib import Path
from struct import pack

from pydicom import dcmread
from pydicom.uid import CTImageStorage, generate_uid


def main():
    source = Path("samples/apex-rebuild-sc.dcm")
    output = Path("samples/apex-synthetic-stack")
    output.mkdir(parents=True, exist_ok=False)

    study_uid = generate_uid()
    series_uid = generate_uid()
    frame_uid = generate_uid()

    for index in range(5):
        image = dcmread(source)
        image.SOPClassUID = CTImageStorage
        image.SOPInstanceUID = generate_uid()
        image.file_meta.MediaStorageSOPClassUID = image.SOPClassUID
        image.file_meta.MediaStorageSOPInstanceUID = image.SOPInstanceUID

        image.PatientID = "APEX-STACK-001"
        image.StudyID = "STACK001"
        image.StudyDescription = "APEX Synthetic Slice Stack"
        image.SeriesDescription = "Five axial test slices"
        image.StudyInstanceUID = study_uid
        image.SeriesInstanceUID = series_uid
        image.FrameOfReferenceUID = frame_uid
        image.Modality = "CT"
        del image.ConversionType

        image.ImageType = ["DERIVED", "SECONDARY", "AXIAL"]
        image.PatientPosition = "HFS"
        image.ImageOrientationPatient = [1, 0, 0, 0, 1, 0]
        image.ImagePositionPatient = [0, 0, 2 * index]
        image.PixelSpacing = [1, 1]
        image.SliceThickness = 2
        image.SpacingBetweenSlices = 2
        image.InstanceNumber = index + 1

        image.BitsAllocated = image.BitsStored = 16
        image.HighBit = 15
        image.PixelRepresentation = 1
        image.RescaleIntercept = 0
        image.RescaleSlope = 1
        image.RescaleType = "HU"
        image.WindowCenter = 0
        image.WindowWidth = 1000

        radius = 12 + 8 * index
        pixels = [
            300 if (x - 64) ** 2 + (y - 64) ** 2 < radius ** 2 else -400
            for y in range(image.Rows)
            for x in range(image.Columns)
        ]
        image.PixelData = pack(f"<{len(pixels)}h", *pixels)
        image["PixelData"].VR = "OW"
        image.save_as(output / f"slice-{index + 1:02}.dcm", enforce_file_format=True)

    print(f"Created 5 slices in {output}")
    print(f"Study Instance UID: {study_uid}")


if __name__ == "__main__":
    main()
