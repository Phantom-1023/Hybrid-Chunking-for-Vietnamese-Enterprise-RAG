# Các chiến lược chunking

## Fixed chunking

Fixed chunking chia văn bản thành các đoạn có kích thước cố định. Cách này đơn giản, dễ kiểm soát và chạy nhanh, nhưng có thể cắt ngang ý nghĩa của câu hoặc đoạn.

## Recursive chunking

Recursive chunking ưu tiên cắt theo cấu trúc tự nhiên như đoạn, câu, dấu xuống dòng, rồi mới cắt nhỏ hơn nếu đoạn quá dài. Cách này thường giữ ngữ cảnh tốt hơn fixed chunking.

## Semantic chunking

Semantic chunking cố gắng chia văn bản theo mức độ gần nghĩa giữa các phần. Trong MVP hiện tại, semantic strategy vẫn tồn tại nhưng có thể dùng fallback nếu xử lý semantic quá nặng hoặc thiếu điều kiện runtime. Khi dùng fallback phải nói rõ, không claim là semantic đầy đủ.

## Paragraph chunking

Paragraph chunking chia theo đoạn văn. Cách này phù hợp khi dữ liệu đã có cấu trúc đoạn rõ ràng, nhưng có thể tạo chunk quá dài hoặc quá ngắn nếu văn bản không đều.

## Vì sao phải so sánh?

Chunking quyết định context nào được đưa vào LLM. Nếu chunk quá nhỏ, câu trả lời thiếu ngữ cảnh. Nếu chunk quá lớn, retrieval bị nhiễu. Vì vậy dự án so sánh 4 cách chunking để tìm phương án phù hợp hơn cho RAG tiếng Việt.
