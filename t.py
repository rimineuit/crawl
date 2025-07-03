import os
import shutil

# Thư mục nguồn (gồm ảnh cần đổi tên)
source_folder = 'merged'
# Thư mục đích (lưu ảnh đã đổi tên)
output_folder = 'rimine_fire'
os.makedirs(output_folder, exist_ok=True)

# Lấy danh sách các ảnh
files = [f for f in os.listdir(source_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
files.sort()  # Sắp xếp để đặt tên theo thứ tự nhất quán

# Sao chép và đổi tên
for idx, filename in enumerate(files, start=1):
    ext = os.path.splitext(filename)[1]  # Giữ phần mở rộng
    new_filename = f"{idx}{ext}"        # Đặt tên mới: 1.jpg, 2.jpg, ...
    
    src_path = os.path.join(source_folder, filename)
    dst_path = os.path.join(output_folder, new_filename)
    
    shutil.copy(src_path, dst_path)

print(f"Đã sao chép và đổi tên {len(files)} ảnh sang thư mục '{output_folder}'")
