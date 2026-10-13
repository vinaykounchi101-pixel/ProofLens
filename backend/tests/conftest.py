"""Pytest fixtures for unit and integration testing."""

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import pypdf
from app.main import app
from app.core.database import Base, engine


@pytest.fixture(scope="session")
def sample_pdf_bytes() -> bytes:
    """Generates a real, valid 2-page PDF in-memory for testing."""
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R 4 0 R] /Count 2>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 6 0 R>> endobj\n"
        b"4 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 5 0 R >> >> /Contents 7 0 R>> endobj\n"
        b"5 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"6 0 obj <</Length 108>> stream\n"
        b"BT\n/F1 12 Tf\n72 712 Td\n(Total net sales were 81797 million dollars for the third quarter period.) Tj\nET\n"
        b"endstream endobj\n"
        b"7 0 obj <</Length 110>> stream\n"
        b"BT\n/F1 12 Tf\n72 712 Td\n(Employees must provide 30 calendar days written notice prior to departure.) Tj\nET\n"
        b"endstream endobj\n"
        b"xref\n0 8\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n0000000222 00000 n \n0000000329 00000 n \n0000000392 00000 n \n0000000551 00000 n \n"
        b"trailer <</Size 8 /Root 1 0 R>>\nstartxref\n712\n%%EOF"
    )
    return pdf_content


@pytest.fixture(scope="session")
def second_sample_pdf_bytes() -> bytes:
    """Generates a second 1-page PDF with contrasting policy terms for comparison testing."""
    pdf_content = (
        b"%PDF-1.4\n"
        b"1 0 obj <</Type /Catalog /Pages 2 0 R>> endobj\n"
        b"2 0 obj <</Type /Pages /Kids [3 0 R] /Count 1>> endobj\n"
        b"3 0 obj <</Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R>> endobj\n"
        b"4 0 obj <</Type /Font /Subtype /Type1 /BaseFont /Helvetica>> endobj\n"
        b"5 0 obj <</Length 160>> stream\n"
        b"BT\n/F1 12 Tf\n72 712 Td\n(Senior managers are required to submit notice at least 60 days in advance.) Tj\n0 -20 Td\n(This policy supersedes all prior guidelines.) Tj\nET\n"
        b"endstream endobj\n"
        b"xref\n0 6\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000109 00000 n \n0000000216 00000 n \n0000000279 00000 n \n"
        b"trailer <</Size 6 /Root 1 0 R>>\nstartxref\n490\n%%EOF"
    )
    return pdf_content


@pytest_asyncio.fixture
async def async_client():
    # Setup test tables freshly
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        yield client

