# Kịch bản nói theo slide

## Slide 1: Tên đề tài

**Nói trong 30-60 giây:**  
Chào thầy/cô, đề tài của nhóm là hệ thống RAG cho quản lý tri thức doanh nghiệp trong bối cảnh tiếng Việt. Ở giai đoạn MVP, nhóm tập trung vào phần lõi: lấy dataset public tiếng Việt, chia văn bản bằng 4 chiến lược chunking, lưu vào ChromaDB, truy xuất theo câu hỏi và hiển thị câu trả lời kèm nguồn. Mục tiêu hiện tại là demo được và có số liệu đánh giá ban đầu, không dùng số liệu giả.

**Chuyển tiếp:** Để thấy vì sao cần hệ thống này, em xin đi từ vấn đề chính.

**Không overclaim:** Không nói hệ thống đã production-ready.

## Slide 2: Vấn đề

**Nói trong 30-60 giây:**  
Với tài liệu nghiệp vụ tiếng Việt, câu hỏi của người dùng thường cần đúng đoạn nguồn. Nếu chỉ hỏi LLM trực tiếp, mô hình có thể trả lời tự tin nhưng thiếu căn cứ. RAG giải quyết bằng cách truy xuất đoạn liên quan trước, sau đó LLM chỉ trả lời dựa trên context được cung cấp. Vì vậy source chunks là phần rất quan trọng trong demo của nhóm.

**Chuyển tiếp:** Từ vấn đề đó, nhóm đặt câu hỏi nghiên cứu về chunking.

**Không overclaim:** Không nói RAG loại bỏ hoàn toàn hallucination.

## Slide 3: Câu hỏi nghiên cứu

**Nói trong 30-60 giây:**  
Câu hỏi nghiên cứu của nhóm là: với dữ liệu tiếng Việt, chiến lược chunking nào giúp hệ thống RAG truy xuất đúng ngữ cảnh hơn? Nhóm so sánh 4 chiến lược: fixed, recursive, semantic và paragraph. Mỗi chiến lược được index vào một collection riêng để khi truy vấn có thể so sánh hành vi retrieval.

**Chuyển tiếp:** Cách làm này cũng phản hồi trực tiếp các góp ý ở Review 1.

**Không overclaim:** Không nói đã có kết luận học thuật cuối cùng khi chưa có full RAGAS.

## Slide 4: Phản hồi Review 1

**Nói trong 30-60 giây:**  
Ở Review 1, nhóm nhận feedback quan trọng: dataset không nên phụ thuộc doanh nghiệp, cần có prototype website, và pipeline phải rõ. MVP hiện tại phản hồi các điểm đó bằng cách dùng dataset public `sailor2/Vietnamese_RAG`, có Streamlit demo, và có luồng verify, index, query, evaluation-lite. Những phần như hybrid search hay upload file doanh nghiệp được giữ lại cho hướng mở rộng để tránh mở scope quá rộng.

**Chuyển tiếp:** Em sẽ nói rõ hơn về dataset đang dùng.

**Không overclaim:** Không nói đã xử lý xong yêu cầu hybrid search/reranking.

## Slide 5: Dataset

**Nói trong 30-60 giây:**  
Dataset nhóm dùng là `sailor2/Vietnamese_RAG`, config `BKAI_RAG`. Đây là dataset public nên phù hợp với góp ý về backup dataset và không phụ thuộc quyền dữ liệu doanh nghiệp. Trong UI, nhóm có phần demo với dữ liệu thật: có record_id, câu hỏi gốc, ground truth và context preview. Điều này giúp chứng minh demo không chỉ là câu hỏi khóa cứng.

**Chuyển tiếp:** Từ dataset này, hệ thống đi qua pipeline RAG như sau.

**Không overclaim:** Không nói dataset này đại diện hoàn toàn cho mọi tài liệu doanh nghiệp.

## Slide 6: Kiến trúc MVP

**Nói trong 30-60 giây:**  
Pipeline gồm các bước: load dataset, join context, chia chunk theo 4 strategy, embed bằng Gemini, lưu vào ChromaDB theo 4 collection, sau đó khi người dùng hỏi thì embed câu hỏi, retrieve top-k chunks và dùng LLM sinh câu trả lời. Streamlit hiển thị cả answer và source chunks để người dùng kiểm tra căn cứ.

**Chuyển tiếp:** Phần quan trọng trong pipeline là 4 cách chunking.

**Không overclaim:** Không nói kiến trúc đã tối ưu production.

## Slide 7: Bốn chiến lược chunking

**Nói trong 30-60 giây:**  
Fixed chunking đơn giản và ổn định nhưng có thể cắt ngang ý. Recursive cố gắng giữ cấu trúc tự nhiên hơn. Semantic hướng tới chia theo nghĩa, nhưng trong MVP có fallback để đảm bảo demo chạy được. Paragraph chia theo đoạn văn, phù hợp khi context đã có cấu trúc đoạn rõ. Mỗi cách có trade-off nên cần benchmark thay vì chọn theo cảm tính.

**Chuyển tiếp:** Hiện MVP đã chạy được những phần nào?

**Không overclaim:** Nếu thầy hỏi semantic, nói rõ hiện có fallback.

## Slide 8: Trạng thái đã hoàn thành

**Nói trong 30-60 giây:**  
Tới hiện tại, nhóm đã hoàn thành các mốc chính cho MVP: verify dataset và chunking, index vào ChromaDB, CLI query, Streamlit UI, demo record thật từ dataset public, và benchmark evaluation-lite. Điều này đủ để nhóm demo end-to-end: từ dữ liệu thật đến câu trả lời có source chunks.

**Chuyển tiếp:** Sau đây là giao diện demo nhóm dùng để trình bày.

**Không overclaim:** Không nói full RAGAS đã hoàn thành.

## Slide 9: Demo UI

**Nói trong 30-60 giây:**  
Giao diện Streamlit có sidebar chọn strategy và top-k. Tab hỏi thủ công cho phép nhập câu hỏi. Tab demo dữ liệu thật cho phép chọn hoặc random record từ dataset public. Tab benchmark hiển thị kết quả evaluation-lite từ CSV thật. Trong demo live, nhóm sẽ ưu tiên tab dữ liệu thật để chứng minh câu hỏi không bị khóa cứng.

**Chuyển tiếp:** Khi có câu trả lời, phần quan trọng nhất là source chunks.

**Không overclaim:** Không gọi UI là sản phẩm doanh nghiệp hoàn chỉnh.

## Slide 10: Source chunks

**Nói trong 30-60 giây:**  
Source chunks là bằng chứng cho câu trả lời. Khi hệ thống trả lời, người xem có thể mở từng chunk để kiểm tra câu trả lời dựa vào đoạn nào. Metadata giúp truy vết record và chunk. Đây là điểm quan trọng để bảo vệ câu trả lời của RAG, nhất là khi so sánh với LLM trả lời trực tiếp.

**Chuyển tiếp:** Tiếp theo là kết quả benchmark nhỏ mà nhóm đã chạy.

**Không overclaim:** Không nói source chunks đảm bảo answer luôn đúng 100%.

## Slide 11: Evaluation-lite benchmark

**Nói trong 30-60 giây:**  
Nhóm đã chạy evaluation-lite trên 5 sample để có tín hiệu benchmark thật. Đây chưa phải full RAGAS. Kết quả hiện tại: paragraph có `avg_score` cao nhất là 0.8354; recursive 0.3410; fixed 0.3344; semantic 0.3313. Số này giúp kiểm tra nhanh retrieval behavior của MVP và dùng làm căn cứ demo ban đầu.

**Chuyển tiếp:** Để tránh hiểu nhầm, em giải thích các metric này đo gì.

**Không overclaim:** Không nói paragraph chắc chắn là strategy tốt nhất về mặt học thuật.

## Slide 12: Cách đọc số benchmark

**Nói trong 30-60 giây:**  
Evaluation-lite dùng các proxy metric. `top1_hit_rate` kiểm tra chunk đầu có cùng record với câu hỏi không. `topk_hit_rate` kiểm tra trong top-k có chunk đúng record không. `avg_distance` là khoảng cách retrieval trung bình. `answer_keyword_overlap` ở lần chạy này dùng retrieved source chunks để so với ground truth, vì nhóm tắt LLM generation trong benchmark để tránh quota và treo máy. `avg_score` là điểm tổng hợp để nhìn nhanh.

**Chuyển tiếp:** Vì đây chỉ là benchmark nhỏ, nhóm có các giới hạn cần nói rõ.

**Không overclaim:** Nhấn mạnh evaluation-lite không thay thế RAGAS.

## Slide 13: Giới hạn hiện tại

**Nói trong 30-60 giây:**  
Nhóm minh bạch các giới hạn hiện tại. Full RAGAS chưa chạy. Evaluation-lite chỉ dùng 5 sample. Semantic chunking có fallback. Embedding đang dùng execution patch `gemini-embedding-001` vì API key hiện tại không hỗ trợ `text-embedding-004`. Upload tài liệu doanh nghiệp thật cũng chưa nằm trong MVP.

**Chuyển tiếp:** Tuy vậy, hướng Enterprise vẫn rõ ràng cho phase sau.

**Không overclaim:** Không che giấu execution patch hoặc gọi evaluation-lite là RAGAS.

## Slide 14: Tầm nhìn Enterprise

**Nói trong 30-60 giây:**  
MVP hiện tại chứng minh phần lõi RAG. Nếu mở rộng thành Enterprise RAG thật, hệ thống sẽ cần upload và batch ingestion tài liệu doanh nghiệp, metadata nâng cao, phân quyền, audit log, monitoring, cache, hybrid search, reranking hoặc GraphRAG. Những phần này là future work, không phải phần đã hoàn thành trong MVP.

**Chuyển tiếp:** Cuối cùng là kết luận và bước tiếp theo.

**Không overclaim:** Không nói đã có phân quyền, upload, hybrid search hay GraphRAG.

## Slide 15: Kết luận và bước tiếp theo

**Nói trong 30-60 giây:**  
Tóm lại, MVP đã chạy end-to-end trên dataset public tiếng Việt: verify, index, query, Streamlit demo, real dataset demo và evaluation-lite benchmark. Nhóm đã có bằng chứng demo và benchmark nhỏ thật, không dùng số liệu giả. Bước tiếp theo là chạy full RAGAS khi ổn định dependency/quota, hoàn thiện report và slide final.

**Chuyển tiếp:** Em xin chuyển sang phần demo hoặc Q&A.

**Không overclaim:** Kết luận ở mức MVP, không gọi đây là sản phẩm cuối.
