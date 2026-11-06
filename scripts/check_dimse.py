import argparse
from email import policy
from email.parser import BytesParser
from io import BytesIO
from urllib.request import Request, urlopen

from pydicom import dcmread
from pydicom.uid import generate_uid
from pynetdicom import AE
from pynetdicom.sop_class import Verification


def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def send(command, image):
    sender = AE(ae_title="APEXDEV")
    sender.acse_timeout = sender.dimse_timeout = sender.network_timeout = 10
    if command == "echo":
        sender.add_requested_context(Verification)
    else:
        sender.add_requested_context(image.SOPClassUID, image.file_meta.TransferSyntaxUID)

    association = sender.associate("orthanc", 4242, ae_title="ORTHANC")
    require(association.is_established, "could not associate with ORTHANC")
    operation = f"C-{command.upper()}"
    try:
        if command == "echo":
            response = association.send_c_echo()
        else:
            response = association.send_c_store(image)
        status = getattr(response, "Status", None)
        detail = "no status" if status is None else f"0x{status:04X}"
        require(status == 0, f"{operation} returned {detail}")
        print(f"PASS: {operation} returned {detail}", flush=True)
    finally:
        if association.is_established:
            association.release()


def prepare_fixture():
    image = dcmread("/fixture.dcm")
    require(image.PatientID == "APEX-REBUILD-001", "expected the synthetic rebuild fixture")
    image.PatientID = "APEX-DIMSE-001"
    image.StudyID = "DIMSE001"
    image.StudyDescription = "APEX Synthetic C-STORE"
    for attribute in ("StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID"):
        original_uid = str(getattr(image, attribute))
        uid = generate_uid(entropy_srcs=["APEX-CSTORE-v1", attribute, original_uid])
        setattr(image, attribute, uid)
    image.file_meta.MediaStorageSOPInstanceUID = image.SOPInstanceUID
    return image


def verify_retrieval(image):
    url = (
        f"http://orthanc:8042/dicom-web/studies/{image.StudyInstanceUID}"
        f"/series/{image.SeriesInstanceUID}/instances/{image.SOPInstanceUID}"
    )
    request = Request(url, headers={"Accept": 'multipart/related; type="application/dicom"'})
    with urlopen(request, timeout=10) as response:
        content_type = response.headers["Content-Type"]
        require(response.status == 200 and content_type, "expected HTTP 200 with a Content-Type")
        headers = f"Content-Type: {content_type}\r\n\r\n".encode("ascii")
        message = BytesParser(policy=policy.default).parsebytes(headers + response.read())

    require(message.get_content_type() == "multipart/related", "expected multipart/related")
    parts = list(message.iter_parts())
    require(len(parts) == 1, f"expected one response part, got {len(parts)}")
    require(parts[0].get_content_type() == "application/dicom", "expected a DICOM part")
    payload = parts[0].get_payload(decode=True)
    require(bool(payload), "received an empty DICOM part")
    retrieved = dcmread(BytesIO(payload))
    for attribute in ("StudyInstanceUID", "SeriesInstanceUID", "SOPInstanceUID", "PixelData"):
        require(
            getattr(retrieved, attribute, None) == getattr(image, attribute),
            f"retrieved {attribute} differs from the sent image",
        )
    print("PASS: WADO-RS returned the C-STORE instance with matching UIDs and pixel bytes")


def main():
    parser = argparse.ArgumentParser(description="Check DIMSE on the APEX PACS rebuild network")
    parser.add_argument("command", choices=("echo", "store"))
    command = parser.parse_args().command
    image = prepare_fixture() if command == "store" else None
    send(command, image)
    if image is not None:
        verify_retrieval(image)


if __name__ == "__main__":
    main()
