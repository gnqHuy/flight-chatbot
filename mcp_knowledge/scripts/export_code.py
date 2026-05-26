import os

# ==========================================
# CẤU HÌNH ĐƯỜNG DẪN & BỘ LỌC
# ==========================================
PROJECT_DIR = "./"  # Chỉ quét thư mục 'app' chứa logic chính (Backend)
OUTPUT_FILE = "prompt_source_code.txt" # Tên file xuất ra để ném cho LLM

# Các thư mục rác/thư viện KHÔNG quét
IGNORE_DIRS = {'__pycache__', 'venv', 'env', '.git', '.idea', '.vscode', 'node_modules', 'logs', 'scripts' }

# Đuôi file được phép đọc (Bỏ qua ảnh, pdf, mp4...)
ALLOWED_EXTENSIONS = {'.py', '.md', '.json', '.yaml', '.yml'}

# Các file cụ thể cần chặn (Đặc biệt là file bảo mật và file data quá to)
IGNORE_FILES = {
    '.env', 
    'test_case_all.json', 
    'test_report_search_flight.json'
}

def is_valid_file(filepath, filename):
    if filename in IGNORE_FILES:
        return False
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    return True

def export_project_to_txt():
    print(f"🔍 Đang quét thư mục: {PROJECT_DIR}...")
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as out_file:
        out_file.write("=== CẤU TRÚC THƯ MỤC DỰ ÁN ===\n")
        
        # 1. Ghi cấu trúc thư mục dạng Tree
        for root, dirs, files in os.walk(PROJECT_DIR):
            # Lọc bỏ thư mục rác ngay từ đầu
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            level = root.replace(PROJECT_DIR, '').count(os.sep)
            indent = ' ' * 4 * level
            out_file.write(f"{indent}[{os.path.basename(root)}/]\n")
            
            subindent = ' ' * 4 * (level + 1)
            for f in files:
                if is_valid_file(os.path.join(root, f), f):
                    out_file.write(f"{subindent}{f}\n")
                    
        out_file.write("\n\n" + "="*60 + "\n")
        out_file.write("=== CHI TIẾT NỘI DUNG SOURCE CODE ===\n")
        out_file.write("="*60 + "\n\n")
        
        # 2. Đọc và ghi nội dung từng file
        file_count = 0
        for root, dirs, files in os.walk(PROJECT_DIR):
            dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
            
            for filename in files:
                filepath = os.path.join(root, filename)
                if is_valid_file(filepath, filename):
                    relative_path = os.path.relpath(filepath, start=PROJECT_DIR)
                    
                    out_file.write(f"{'='*60}\n")
                    out_file.write(f"FILE: app/{relative_path}\n")
                    out_file.write(f"{'='*60}\n")
                    
                    try:
                        with open(filepath, 'r', encoding='utf-8') as code_file:
                            out_file.write(code_file.read())
                    except Exception as e:
                        out_file.write(f"// ❌ Lỗi không thể đọc file: {e}\n")
                    
                    out_file.write("\n\n")
                    file_count += 1
                    
    print(f"✅ Hoàn tất! Đã gom {file_count} file code vào: {OUTPUT_FILE}")

if __name__ == "__main__":
    export_project_to_txt()