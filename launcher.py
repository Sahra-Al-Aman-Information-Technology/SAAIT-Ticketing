import subprocess
import time
import webbrowser

def main():
    try:
        # Start the Flask app in a subprocess
        subprocess.Popen(["python", "app.py"])

        # Wait a bit to let the server start
        time.sleep(2)

        # Open the web browser to the app URL
        webbrowser.open("http://127.0.0.1:5000")

    except Exception as e:
        print(f"Error launching app: {e}")

if __name__ == "__main__":
    main()
