import sys
import os
import argparse
from ocr import extract_text_from_image
from matcher import process_extracted_lines
from students import MASTER_STUDENTS

def run_checker(image_paths: list[str]):
    print("\n=======================================================")
    print("      ME 104 POLL ATTENDANCE & VOTER CHECKER          ")
    print("=======================================================\n")
    
    if not image_paths:
        print("[!] No images provided.")
        return

    all_lines = []
    for idx, img_path in enumerate(image_paths, 1):
        if not os.path.exists(img_path):
            print(f"[!] Warning: File does not exist: {img_path}")
            continue
        print(f"[{idx}/{len(image_paths)}] Running OCR on: {os.path.basename(img_path)}...")
        lines = extract_text_from_image(img_path)
        all_lines.extend(lines)

    print(f"\n[+] Total raw lines extracted: {len(all_lines)}")
    print("[*] Matching lines against batch aliases & official roster...")
    matched, remaining, unmapped = process_extracted_lines(all_lines)

    total_batch = len(MASTER_STUDENTS)
    total_voted = len(matched)
    total_remaining = len(remaining)

    print("\n" + "=" * 60)
    print(f"📊 SUMMARY: BATCH={total_batch} | VOTED={total_voted} | REMAINING={total_remaining}")
    print("=" * 60)

    if remaining:
        print(f"\n❌ REMAINING / NOT VOTED ({len(remaining)} Students):")
        print("-" * 60)
        print(f"{'Sl':<4} | {'Roll No':<11} | {'Official Name':<35}")
        print("-" * 60)
        for i, s in enumerate(remaining, 1):
            print(f"{i:<4} | {s['roll']:<11} | {s['name']:<35}")
        print("-" * 60)
    else:
        print("\n🎉 ALL 60 STUDENTS IN THE BATCH HAVE VOTED!")

    if unmapped:
        print(f"\nℹ️ Unrecognized Entries (External / Noise, {len(unmapped)}):")
        for u in set(unmapped):
            print(f"  - {u}")

    print("\nDone.\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="ME 104 Poll Attendance Checker")
    parser.add_argument("images", nargs="*", help="Paths to screenshot images")
    parser.add_argument("--folder", "-f", help="Directory containing screenshots")

    args = parser.parse_args()
    imgs = list(args.images) if args.images else []

    if args.folder and os.path.isdir(args.folder):
        for f in os.listdir(args.folder):
            if f.lower().endswith((".png", ".jpg", ".jpeg", ".webp")):
                imgs.append(os.path.join(args.folder, f))

    if not imgs:
        print("Usage: python cli.py <image1.png> <image2.jpg> ...")
        print("   or: python cli.py --folder C:\\path\\to\\screenshots")
        sys.exit(1)

    run_checker(imgs)
