import asyncio
import httpx
from app.main import app


async def test_auth_and_rbac():
    transport = httpx.ASGITransport(app=app)
    async with httpx.AsyncClient(transport=transport, base_url="http://testserver/api/v1") as client:
        # 1. Test Login HR
        hr_resp = await client.post(
            "/auth/login",
            json={"email": "hr@company.com", "password": "hr123456"},
        )
        print("HR Login Status:", hr_resp.status_code)
        assert hr_resp.status_code == 200, f"HR login failed: {hr_resp.text}"
        hr_data = hr_resp.json()
        hr_token = hr_data["access_token"]
        assert hr_data["user"]["role"] == "hr"
        print("HR token received successfully, role =", hr_data["user"]["role"])

        # 2. Test Login Employee
        emp_resp = await client.post(
            "/auth/login",
            json={"email": "employee@company.com", "password": "employee123456"},
        )
        print("Employee Login Status:", emp_resp.status_code)
        assert emp_resp.status_code == 200, f"Employee login failed: {emp_resp.text}"
        emp_data = emp_resp.json()
        emp_token = emp_data["access_token"]
        assert emp_data["user"]["role"] == "employee"
        print("Employee token received successfully, role =", emp_data["user"]["role"])

        # 3. Test RBAC: Employee attempts to upload document (should get 403 Forbidden)
        files = {"files": ("test_policy.txt", b"Employee benefits test content", "text/plain")}
        emp_upload = await client.post(
            "/documents/upload",
            headers={"Authorization": f"Bearer {emp_token}"},
            files=files,
        )
        print("Employee Upload Status (Expected 403):", emp_upload.status_code)
        assert emp_upload.status_code == 403, f"Expected 403, got {emp_upload.status_code}: {emp_upload.text}"
        print("RBAC verified: Employee is properly blocked from uploading documents with 403 Forbidden!")

        # 4. Test RBAC: Unauthenticated upload (should get 401 Unauthorized)
        anon_upload = await client.post(
            "/documents/upload",
            files={"files": ("test_policy.txt", b"Test", "text/plain")},
        )
        print("Unauthenticated Upload Status (Expected 401):", anon_upload.status_code)
        assert anon_upload.status_code == 401, f"Expected 401, got {anon_upload.status_code}"
        print("RBAC verified: Unauthenticated request rejected with 401 Unauthorized!")

        # 5. Test Chat as Employee (allowed)
        emp_chat = await client.post(
            "/chat",
            headers={"Authorization": f"Bearer {emp_token}"},
            json={"query": "What are the standard working hours?"},
        )
        print("Employee Chat Status (Expected 200):", emp_chat.status_code)
        assert emp_chat.status_code == 200, f"Expected 200, got {emp_chat.status_code}: {emp_chat.text}"
        print("Chat verified: Employee can chat seamlessly!")

        print("\nALL AUTH & RBAC TESTS PASSED WITH 100% SUCCESS!")


if __name__ == "__main__":
    asyncio.run(test_auth_and_rbac())
