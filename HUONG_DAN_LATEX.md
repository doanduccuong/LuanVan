# Build và xem trực tiếp báo cáo LaTeX

## Mở dự án

1. Mở thư mục `Do An` bằng VS Code.
2. Cài extension được VS Code đề xuất: **LaTeX Workshop**.
3. Mở file `BAO CAO/LuanVan.tex`.
4. Lưu file (`Cmd+S`). LaTeX Workshop sẽ tự chạy `latexmk`.

PDF được tạo tại `output/pdf/LuanVan.pdf`. Chọn biểu tượng **View LaTeX PDF** ở góc phải editor để xem ngay trong một tab VS Code.

## Phím tắt hữu ích

- Build thủ công: mở Command Palette (`Cmd+Shift+P`) và chọn `LaTeX Workshop: Build LaTeX project`.
- Xem PDF: `Cmd+Option+V` khi đang mở file `.tex`.
- Từ PDF quay về dòng LaTeX tương ứng: nhấp đúp vào nội dung PDF.

## Build từ Terminal

```bash
cd "BAO CAO"
latexmk -pdf -synctex=1 -interaction=nonstopmode \
  -file-line-error -outdir="../output/pdf" LuanVan.tex
```

File gốc của toàn bộ báo cáo là `BAO CAO/LuanVan.tex`; nội dung từng chương nằm trong `BAO CAO/Chuong/`.
