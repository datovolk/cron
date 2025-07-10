import subprocess

def run_all_scrapers():
    print("=== Running scrapers ===")
    subprocess.run(["python3", "jobs_ge.py"])
    subprocess.run(["python3", "hr_ge.py"])
    subprocess.run(["python3", "my_jobs_ge.py"])
    print("=== All scrapers completed ===")

if __name__ == "__main__":
    run_all_scrapers()
