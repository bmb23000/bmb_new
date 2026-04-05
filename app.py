import os
import re
import sqlite3
import requests
from flask import Flask, jsonify, Response, request
from flask_cors import CORS
from urllib.parse import unquote

app = Flask(__name__)
CORS(app)

DB_PATH = 'book.db'

# === SQLite Query ===
def query_books(filter_field=None, filter_value=None, skip=0, top=100):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    query = "SELECT * FROM books"
    params = []

    if filter_field and filter_value:
        query += f" WHERE LOWER({filter_field}) = LOWER(?)"
        params.append(filter_value)

    query += " LIMIT ? OFFSET ?"
    params.extend([top, skip])
    cur.execute(query, params)

    rows = cur.fetchall()
    conn.close()
    return [dict(row) for row in rows]

# === OData Endpoint ===
@app.route('/odata/ISBN')
def get_books():
    top = int(request.args.get('$top', 100))
    skip = int(request.args.get('$skip', 0))
    filter_query = request.args.get('$filter')

    field_map = {
        "ISBN_EX": "ISBN_EX",
        "Title": "Title",
        "Author": "Author",
        "Publisher": "Publisher"
    }

    filter_field = filter_value = None
    if filter_query:
        try:
            raw_field, _, raw_value = filter_query.partition(" eq ")
            filter_field = field_map.get(raw_field.strip())
            filter_value = unquote(raw_value.strip("'").strip('"'))
        except Exception as e:
            print("⚠️ Filter parse error:", e)

    result = query_books(filter_field, filter_value, skip, top)

    return jsonify({
        "@odata.context": request.url_root.rstrip('/') + "/odata/$metadata#ISBN",
        "value": result
    })

# === OData Metadata ===
@app.route('/odata/$metadata')
def metadata():
    xml = '''<?xml version="1.0" encoding="utf-8"?>
<edmx:Edmx xmlns:edmx="http://docs.oasis-open.org/odata/ns/edmx" Version="4.0">
  <edmx:DataServices>
    <Schema xmlns="http://docs.oasis-open.org/odata/ns/edm" Namespace="BookModel">
      <EntityType Name="ISBN">
        <Key><PropertyRef Name="ISBN_EX"/></Key>
        <Property Name="ISBN_EX" Type="Edm.String" Nullable="false"/>
        <Property Name="Title" Type="Edm.String"/>
        <Property Name="Author" Type="Edm.String"/>
        <Property Name="PublishDate" Type="Edm.String"/>
        <Property Name="NumberofPages" Type="Edm.String"/>
        <Property Name="CoverImage" Type="Edm.String"/>
        <Property Name="Publisher" Type="Edm.String"/>
      </EntityType>
      <EntityContainer Name="Container">
        <EntitySet Name="ISBN" EntityType="BookModel.ISBN"/>
      </EntityContainer>
    </Schema>
  </edmx:DataServices>
</edmx:Edmx>'''
    return Response(xml, mimetype='application/xml')

@app.route('/')
def home():
    return "✅ SQLite OData API with MediaFire auto-download is live!"

# === Start ===
if __name__ == '__main__':
    
    app.run(host='0.0.0.0', port=10000)

