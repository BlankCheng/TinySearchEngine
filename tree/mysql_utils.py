import pymysql
import json


def mysql_connect(config_path="mysql_config.json"):
    with open(config_path, "r") as f:
        mysql_config = json.load(f)

    print("=" * 35)
    print("Connecting to MySQL database ...")
    for k, v in mysql_config.items():
        if k == "password": continue
        print(f"\t{k}: {v}")

    # 打开数据库连接
    db = pymysql.connect(**mysql_config)

    print("Successfully connected!")
    print("=" * 35)

    return db


def mysql_fetch_main_topic_id(cursor, verbose=0):
    main_topics = [
        "Academic_disciplines",
        "Business",
        "Communication",
        "Concepts",
        "Culture",
        "Economy",
        "Education",
        "Energy",
        "Engineering",
        "Entertainment",
        "Entities",
        "Ethics",
        "Events",
        "Food_and_drink",
        "Geography",
        "Government",
        "Health",
        "History",
        "Human_behavior",
        "Humanities",
        "Information",
        "Internet",
        "Knowledge",
        "Language",
        "Law",
        "Life",
        "Mass_media",
        "Mathematics",
        "Military",
        "Music",
        "Nature",
        "People",
        "Philosophy",
        "Politics",
        "Religion",
        "Science",
        "Society",
        "Sports",
        "Technology",
        "Time",
        "Universe"
    ]
    main_topic_ids = []
    for topic in main_topics:
        sql = f"select page_id from page where page_namespace=14 and page_title='{topic}';"
        try:
            cursor.execute(sql)
            results = cursor.fetchall()
            assert len(results) == 1
            main_topic_ids.append(results[0][0])
            if verbose == 1:
                print(f"[main topic] {topic}, id: {results[0][0]}")
        except:
            print("Error: unable to fetch data")
    return main_topic_ids


def mysql_fetch_parent_page_id(cursor, page_id, verbose=0):
    sql = "select categorylinks.cl_from as p_id, \
           page.page_id as cat_p_id, \
           categorylinks.cl_type as p_type \
           from categorylinks, page \
           where page.page_title=categorylinks.cl_to  \
           and page.page_namespace=14 \
           and categorylinks.cl_from={};"
    sql = sql.format(page_id)

    results = []
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        results = [row[1] for row in results]
        if verbose == 1:
            print(f"[fetch parent] Page {page_id} belongs to {len(results)} categories.")
    except:
        if verbose == 1:
            print("Error: unable to fetch data")

    return results


def mysql_fetch_page_title(cursor, page_id, verbose=0):
    sql = "select page_id, convert(page_title using utf8) from page where page_id={};"
    sql = sql.format(page_id)

    title = ""
    try:
        cursor.execute(sql)
        results = cursor.fetchall()
        assert len(results) == 1
        title = results[0][1]
        if verbose == 1:
            print(f"[fetch title] Title of Page {page_id}: {title}.")
    except:
        if verbose == 1:
            print("Error: unable to fetch data")

    return title


if __name__ == '__main__':
    db = mysql_connect()

    # 使用 cursor() 方法创建一个游标对象 cursor
    cursor = db.cursor()

    cursor.execute("SELECT VERSION()")
    data = cursor.fetchone()
    print("Database version : %s " % data)


    main_topic_ids = mysql_fetch_main_topic_id(cursor, verbose=1)

    print(mysql_fetch_parent_page_id(cursor, page_id=10, verbose=1))
    print(mysql_fetch_page_title(cursor, page_id=10, verbose=1))

    db.close()