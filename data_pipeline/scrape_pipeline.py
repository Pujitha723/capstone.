# Data pipeline for the the Zepton AI/ML capstone

BASE_URL = "https://books.toscrape.com/"
DATA_DIR = Path(__file__).parent
DB_FILE = DATA_DIR / "books.db"
OUTPPUT_FILE = DATA_DIR / "query_outputs.txt"

headers = {"User-Agent": "Mozilla/5.0"}

def get__(url):
    """Dowload one page and return give enough rows for the requirement.
    response = requests.get(url,headers=headers, timeout=20)
    response.raise_for_status()
    return Beautifulsoup(response.text, "html.parser")

def  def scrape_books():
     books = []
     # Five catalogue pages give enough rows for the requirement.
     for page_no in range(1, 6):
         url = BASE_URL + f"catalogue/page-{page_no}.html"
         soup = get_page(url
    
         for item in soup.select("article.product_pod"):
             # First get the link to the individual book page.
             href = item.select_one("h3 a")["href"]
             book_url = BASE_URL + "catalogue/" + href.replace("../", "")
       
             book_soup = get_page(book_url)
       
             title_tag = book_soup.select_one("div.product_main h1")
             price_tag = book_soup.select_one("div.product_main .price_color")
             rating_tag = book_soup.select_one("div.product_main p.star-rating")
             stock_tag = book_soup.select_one(
                 "div.product_main p.instock.availability"
             )
             crumbs = book_soup.select("ul.breadcrumb li")
      
             title = title_tag.get_text(strip=True) if title_tag else None
             price = price_tag.get_text(strip=True) if price_tag else None
             availability = (
                 stock_tag.get_text(" ", strip=True) if stock_tag else None
             )
      
            # The rating is stored as a CSS class such as "Three".
            star_rating = None
            if rating_tag:
               for word in ["One", "Two", "Three", "Four", "Five"]:
                   if word in rating_tag.get("class", []):
                       star_rating = word
                       break
                
           # Breadcrumbs are: Home -> Books -> Category -> Book title
           category = None
           if len(crumbs) >= 3:
              category = crumbs[-2].get_text(strip=True)

          
          books.append({
              "title": title,
              "price": price,
              "star_rating": star_rating,
              "availability": availability,
              "category": category
          })
   return pd.DataFrame(books)


def clean_books(df)
    df = df.copy()
    
    # Remove £ and convert to a number.
    df["price_gbp"] = pd.to_numeric(
        df["price"].astype(str).str.replace("£", "", regex=False),
        errors="coerce"
    )

   rating_numbers = {
      "One": 1,
      "Two": 2,
      "Three": 3,
      "Four": 4,
      "Five": 5
   }
   df["rating"] = df["star_rating"].map(rating_numbers)  
   
   # The website uses text such as "In stock (22 available)".
   df["in_stock"] = (
       df["availability"]
       .fillna("")
       .str.contains("In stock", case=False, regex=False)
   )
   
  # If a numeric value is unexpectedly missing, use the median.
  # This follows the cleaning instruction in the assignment.
  if df["price_gbp"].isna().any():
      df["price_gbp"] = df["price_gbp"].fillna(df["price_gbp"].median())
      
 if df["rating"].isna().any():
     df["rating"] = df["rating"].fillna(df["rating"].median())
     
 # A book without a title/category cannot be used properly in our tables.
 df = df.dropna(subset=["title", "category"])
 
 # Fixed conversion required by the project.
 df["price_inr"] = df["price_gbp"] * GBP_TO_INR
 
 df["price_gbp"] = df["price_gbp"].astype(float)
 df["price_inr"] = df["price_inr"].astype(float)
 df["rating"] = df["rating"].astype(int)
 df["in_stock"] = df["in_stock"].astype(bool)
 
 return df[
     ["title", "price_gbp", "price_inr", "rating", "in_stock", "category"] 
 ]    
   
def create_database(df):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    # Re-running the program should create a clean database.
    cur.execute("DROP TABLE IF EXISTS books")
    cur.execute("DROP TABLE IF EXISTS categories")
    
    cur.execute("""
        CREATE TABLE categories (
            category_id INTEGER PRIMARY KEY,
            category_name TEXT UNIQUE NOT NULL
         )
     """)
     
     cur.execute("""
         CREATE TABLE books (
             book_id INTEGER PRIMARY KEY,
             title TEXT NOT NULL,
             price_gbp REAL NOT NULL,
             price_inr REAL NOT NULL,
             rating INTEGER NOT NULL,
             in_stock INTEGER NOT NULL,
             category_id INTEGER NOT NULL,
             FOREIGN KEY (category_id)
                 REFERENCES categories(category_id)
         )
     """)

    # Insert each category only once.
    categories = sorted(df["category"].unique())
    cur.executemany(
       "INSERT INTO categories (category_name) VALUES (?)",
        [(x,) for x in categories]
    )

    category_ids = dict(
        cur.execute(
            "SELECT category_name, category_id FROM categories"
        ).fetchall()
    )
    
    # Convert True/False to 1/0 because SQLite stores boolean values as integers.
    rows = []
    for row in df.itertuples(index=False):
        rows.append((
        row.title,
           row.price_gbp,
           row.price_inr,
           row.rating,
           int(row.in_stock),
           category_ids[row.category]
        ))
    cur.executemany("""
        INSERT INTO books
        (title, price_gbp, price_inr, rating, in_stock, category_id)
        VALUES (?, ?, ?, ?, ?, ?)
    """, rows)
    
    conn.commit()
    conn.close()
    
def run_sql_queries():
    queries = [
        (
            "Q1 - SELECT, WHERE, ORDER BY, LIMIT",
            """
            SELECT title, price_gbp, rating
            FROM books
            WHERE rating >= 4
            ORDER BY rating DESC, price_gbp ASC
            LIMIT 10;
            """
        ),
        (
            "Q2 - DISTINCT",
            """
            SELECT DISTINCT rating
            FROM books
            ORDER BY rating;
            """
        ),
        (
            "Q3 - BETWEEN",
            """
            SELECT title, price_gbp, price_inr
            FROM books
            WHERE price_gbp BETWEEN 20 AND 40
            ORDER BY price_gbp;
            """
        ),
        (
            "Q4 - IN",
            """
            SELECT title, category_id, rating
            FROM books
            WHERE category_id IN (1, 2, 3) 
            ORDER BY rating DESC
            LIMIT 15;
            """
      ),
      (
             "Q5 - JOIN",
             """
             SELECT c.category_name, b.title, b.rating, b.price_inr
             FROM books b
             JOIN categories c
               ON b.category_id = c.category_id
             ORDER BY c.category_name, b.rating DESC, b.title
             LIMIT 20;
             """
       )
    ]
    conn = sqlite3.connect(DB_FILE)
    saved = []
    
    for name, query in queries:
        result = pd.read_sql_query(query, conn)
        
        print("\n" + name)
        print(result.to_string(index=False))
        
        saved.append(
             name + "\n"
             + query.strip() + "\n\n"
             + result.to_string(index=False)
             + "\n"
        )
    
     conn.close()
 
     OUTPUT_FILE.write_text("\n".join(saved), encoding="utf-8")
     return queries
     
def check_pandas_merge(queries):
     conn = sqlite3.connect(DB_FILE)
     
     # Requirement: read at least two SQL results with pandas.
     q1_df = pd.read_sql_query(queries[0][1], conn)
     sql_join = pd.read_sql_query(queries[4][1], conn)
     
     books_df = pd.read_sql_query("SELECT * FROM books", conn)
     categories_df = pd.read_sql_query(
         "SELECT * FROM categories", conn
     )
     
     conn.close()
     
     print("\nFirst read_sql result:")
     print(q1_df.to_string(index=False))
     
     # Now reproduce the SQL JOIN without SQL.
     merged = books_df.merge(
         categories_df,
         on="category_id",
         how="inner"
      )
    merged = merged[
        ["category_name", "title", "rating", "price_inr"]
    ].sort_values(
        ["category_name", "rating", "title"],
        ascending=[True, False, True]
    ).head(20).reset_index(drop=True)
    
    sql_join = sql_join.reset_index(drop=True)
    
    print("\nSQL JOIN:")
    print(sql_join.to_string(index=False))
    
    print("\npandas.merge:")
    print(merged.to_string(index=False))
    
    print("\nDo SQL JOIN and pandas.merge match?")
    print(merged.equals(sql_join))

    
def main():
    print("Starting data pipeline...")
    
    raw = scrape_books()
    print("Rows scraped:", len(raw))
    
    cleaned = clean_books(raw)
    print("Rows after cleaning:", len(cleaned))
    print("Number of categories:", cleaned["category"].nunique())
    
    # Check the main acceptance requirement before creating the DB.
 
   if len(cleaned) < 60:
       raise ValueError("Less than 60 books were collected.")
     
   if cleaned["category"].nunique() < 3:
       raise ValueError("Less than 3 categories were collected.")
    
    create_database(cleaned)
    queries = run_sql_queries()
    check_pandas_merge(queries)

    print("\nDone.")
    print("Database:", DB_FILE)
    print("Saved query output:", OUTPUT_FILE)
    print("Conversion used: 1 GBP = 105.50 INR")

    
