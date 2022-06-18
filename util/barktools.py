def user_yes_no(prompt: str) -> bool:
    while True:
        ans = input(f"{prompt} (y/n): ")
        if ans.rstrip().lower() in ["y", "yes", "yeboiii"]:
            return True
        elif ans.rstrip().lower() in ["n", "no"]:
            return False
        else:
            print("Invalid response. Enter y or n.")
