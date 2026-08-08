import json
from datasets import load_dataset, concatenate_datasets

# 1. Định nghĩa hàm chuyển đổi format chuẩn RAG
def format_to_chatml(example):
    # Xử lý các trường linh hoạt (từ HF hoặc từ file tự tạo)
    context = example.get('context', example.get('text', ''))
    question = example.get('question', '')
    answer = example.get('answer', '')
    
    prompt = f"Dựa vào các tài liệu sau đây:\n{context}\n\nHãy trả lời câu hỏi: {question}"
    
    return {
        "messages": [
            {"role": "user", "content": prompt},
            {"role": "assistant", "content": answer}
        ]
    }

print("Đang tải dữ liệu từ HuggingFace...")
hf_dataset = load_dataset("NamSyntax/Vietnamese-Legal-QA-RAG", split="train")

print("Đang xử lý dữ liệu nội bộ...")
# Giả sử file của bạn có các trường: question, answer, context
# Nếu file của bạn là CSV thì đổi 'json' thành 'csv'
try:
    custom_dataset = load_dataset("json", data_files="my_custom_data.jsonl", split="train")
    custom_formatted = custom_dataset.map(format_to_chatml, remove_columns=custom_dataset.column_names)
    hf_formatted = hf_dataset.map(format_to_chatml, remove_columns=hf_dataset.column_names)
    
    # Trộn 2 tập dữ liệu
    final_dataset = concatenate_datasets([hf_formatted, custom_formatted])
except Exception as e:
    print(f"Không tìm thấy file custom, chỉ dùng dữ liệu HuggingFace. Lỗi: {e}")
    final_dataset = hf_dataset.map(format_to_chatml, remove_columns=hf_dataset.column_names)

# Trộn ngẫu nhiên (Shuffle)
final_dataset = final_dataset.shuffle(seed=42)

# Xuất ra file để đưa lên Colab
output_file = "training_rag_data.jsonl"
final_dataset.to_json(output_file, force_ascii=False)
print(f"✅ Đã tạo thành công {len(final_dataset)} mẫu dữ liệu RAG-Aware vào file: {output_file}")