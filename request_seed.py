import requests
import json

API_URL = "https://eajeyq4r3zljoq4rpovy2nthda0vtjqf.lambda-url.ap-south-1.on.aws"

def request_seed(student_id: str, github_repo_url: str):
    # Read student public key
    with open("student_public.pem", "r") as f:
        public_key_pem = f.read()

    # Convert to single-line (replace real newlines with literal \n)
    public_key_single_line = public_key_pem.replace("\n", "\\n")

    payload = {
        "student_id": "22A91A4466",
        "github_repo_url": "https://github.com/divyasrisaipravallika/Build-Secure-PKI-Based-2FA-Microservice-with-Docker",
        "public_key": "-----BEGIN PUBLIC KEY-----\nMIICIjANBgkqhkiG9w0BAQEFAAOCAg8AMIICCgKCAgEAkP7mtjQLPWr+gIAStKSV\n+PThf2qibcDevQYb+XLFcv7z+uJprgeOsMRz5QP7Idn1irFca45jUAnFKatj8JNw\nWKb4iyvVNaRXHYqit9CfVhTAVNsubvpfu6j4p3bj5RlsZyUyxjSgtuyD0eD3neD4\nA1qA/aJlPl7XxJ6M4xUMuwWh3fKEwTm31/UIq1zIFc5chIo0sQIHvrjHZNGtf3hg\n+B/zAbwTCxWYlHIPqKZgo1NWl/SP416wNQ5VSTipO2eaCs95qz9pFSVbHzmJ6MHS\n6qfKocR2Km4JOQSnLSdbS060lhrWhkuIqqIeHgtqvvn4hOwewtNaxQFnMizaEAQY\nIPEd+EbhNmZLv5ASK07W6ceSla0KjSluY1vIcRAhwI24nk80ljFhjrkJUeWmo3n/\nDeQAwlQ5z1/tutIzlH0aGFGQPrwR/ob5PEIu1AZYHSllm5ZEhWwCgaXFQZhc3atm\n7qPTpZ5/2CreBDP9xwU7WMpnX9SCtvR5gIeVT7EUY08/4rRdWgqhzywKxIKiE87b\nheBhq+Pc+/EKBhEyL+AMqDVTMJnk2VZlKkpDuiI1IxqgvO5lX7tNHOtMwagYp5X8\nIwIh75WClnBNX6KWNUoNZrOdjvzg4f5uXSMZwhF9bmjBovEKdE68bEJh++jOo/ew\nFBxf8rkad+MeLEP4DciQNykCAwEAAQ==\n-----END PUBLIC KEY-----\n"
    }

    print("\nSending request to instructor API...\n")
    response = requests.post(API_URL, json=payload, timeout=15)

    if response.status_code != 200:
        print("❌ Error:", response.text)
        return

    data = response.json()

    if data.get("status") != "success":
        print("❌ API returned an error:", data)
        return

    encrypted_seed = data.get("encrypted_seed")

    if not encrypted_seed:
        print("❌ No encrypted seed found in API response.")
        return

    # Save encrypted seed to file
    with open("encrypted_seed.txt", "w") as f:
        f.write(encrypted_seed)

    print("✅ Encrypted seed received and saved to encrypted_seed.txt")
    print("⚠️ Do NOT commit this file to Git!")


if __name__ == "__main__":
    request_seed(
        student_id="YOUR_STUDENT_ID",
        github_repo_url="https://github.com/<your-username>/Build-Secure-PKI-Based-2FA-Microservice-with-Docker"
    )
