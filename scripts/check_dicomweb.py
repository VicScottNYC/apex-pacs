import json
from email import policy
from email.parser import BytesParser
from urllib.request import Request, urlopen

from io import BytesIO
from pathlib import Path

from pydicom import dcmread


BASE = "http://127.0.0.1:8043/dicom-web"

FIXTURE_DIR = (
    Path(__file__).resolve().parents[1] / "samples" / "apex-synthetic-stack"
)

def require(condition, message):
    if not condition:
        raise SystemExit(f"FAIL: {message}")


def main():
    query = Request(
        f"{BASE}/studies?PatientID=APEX-STACK-001",
        headers={"Accept": "application/dicom+json"},
    )
    with urlopen(query, timeout=10) as response:
        studies = json.load(response)

    require(len(studies) == 1, f"expected one matching study, got {len(studies)}")
    study = studies[0]
    uid = study["0020000D"]["Value"][0]
    require(study["00201206"]["Value"] == [1], "expected one series")
    require(study["00201208"]["Value"] == [5], "expected five instances")
    print(f"PASS: QIDO-RS found {uid} with one series and five instances")

    retrieve = Request(
        f"{BASE}/studies/{uid}",
        headers={"Accept": 'multipart/related; type="application/dicom"'},
    )
    with urlopen(retrieve, timeout=10) as response:
        require(response.status == 200, f"expected HTTP 200, got {response.status}")
        content_type = response.headers["Content-Type"]
        body = response.read()

    require(content_type is not None, "missing WADO-RS Content-Type")
    headers = f"Content-Type: {content_type}\r\nMIME-Version: 1.0\r\n\r\n"
    message = BytesParser(policy=policy.default).parsebytes(
        headers.encode("ascii") + body
    )
    require(message.get_content_type() == "multipart/related", "expected multipart/related")
    parts = list(message.iter_parts())
    require(len(parts) == 5, f"expected five response parts, got {len(parts)}")
    expected = {}
    for fixture in sorted(FIXTURE_DIR.glob("slice-*.dcm")):
        image = dcmread(fixture)
        expected[image.SOPInstanceUID] = image

    require(len(expected) == 5, "expected five distinct local fixture instances")

    for part in parts:
        require(part.get_content_type() == "application/dicom", "expected a DICOM part")
        payload = part.get_payload(decode=True)
        require(bool(payload), "received an empty DICOM part")

        image = dcmread(BytesIO(payload))
        instance_uid = image.SOPInstanceUID
        original = expected.pop(instance_uid, None)
        require(original is not None, f"unexpected or duplicate instance {instance_uid}")
        require(image.StudyInstanceUID == uid, f"wrong study for {instance_uid}")

        for attribute in (
            "SeriesInstanceUID",
            "InstanceNumber",
            "ImagePositionPatient",
            "ImageOrientationPatient",
            "PixelSpacing",
            "PixelData",
        ):
            require(
                getattr(image, attribute, None) == getattr(original, attribute),
                f"{attribute} differs for {instance_uid}",
            )

    require(not expected, f"missing instances: {list(expected)}")
    print("PASS: WADO-RS returned all five original slices with matching geometry and pixels")


if __name__ == "__main__":
    main()
