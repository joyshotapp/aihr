import json

data = json.load(open(r'C:\Users\User\Desktop\legal\datasets\ch\law\data.json', 'r', encoding='utf-8-sig'))

# Extract full text of key laws for compliance
target_laws = ['個人資料保護法', '消費者保護法', '電子簽章法']
for law in data['Laws']:
    if law['LawName'] in target_laws:
        print(f"\n{'='*60}")
        print(f"法律名稱: {law['LawName']}")
        print(f"最後修正: {law['LawModifiedDate']}")
        print(f"{'='*60}")
        for art in law['LawArticles']:
            if art['ArticleType'] == 'A':
                print(f"\n{art['ArticleNo']}")
                print(art['ArticleContent'])
            elif art['ArticleType'] == 'C':
                print(f"\n{art['ArticleContent']}")
