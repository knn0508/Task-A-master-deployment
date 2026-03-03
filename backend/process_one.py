from simple_app import create_simple_app

# create_app returns app, db_manager, rag_service
app, db_manager, rag_service, chat_service = create_simple_app()

doc_id = 5
doc_path = db_manager.execute_query(
    "SELECT file_path FROM documents WHERE id = ?",
    (doc_id,),
    fetch_one=True
)

if not doc_path:
    print("❌ Sənəd tapılmadı.")
    exit()

file_path = doc_path['file_path']

print(f"➡️ Processing document ID {doc_id}: {file_path}")
ok = rag_service.process_document(file_path, doc_id)

if ok:
    print("✅ Sənəd uğurla işlənildi.")
else:
    print("❌ İşləmə zamanı xəta baş verdi.")