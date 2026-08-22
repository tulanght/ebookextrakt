import os

def remove_empty_folders(path):
    for root, dirs, files in os.walk(path, topdown=False):
        for name in dirs:
            dir_path = os.path.join(root, name)
            if not os.listdir(dir_path): # Check if directory is empty
                try:
                    os.rmdir(dir_path)
                    print(f"Removed empty directory: {dir_path}")
                except Exception as e:
                    print(f"Could not remove {dir_path}: {e}")

if __name__ == "__main__":
    remove_empty_folders(r"D:\Ebooks")
