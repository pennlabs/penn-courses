#!/usr/bin/env python
"""
Populate pgvector table with course embeddings.

Usage:
    export OPENAI_API_KEY=your_key
    export DATABASE_URL=postgres://penn-courses:postgres@localhost:5432/postgres
    uv run python populate_pgvector.py --limit 10
"""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'PennCourses.settings.development')

import django
django.setup()

from django.db import connection
from courses.models import Course
from review.views import course_filters_pcr
from openai import OpenAI
import psycopg2
from psycopg2.extras import execute_values

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    print("ERROR: OPENAI_API_KEY not set")
    sys.exit(1)

client = OpenAI(api_key=api_key)

def create_course_text(course):
    """Build searchable text from course"""
    text_parts = []
    if course.title:
        text_parts.append(course.title)
    if course.description:
        text_parts.append(course.description)
    if course.department:
        text_parts.append(course.department.name)
    
    instructors = set()
    for section in course.sections.all()[:5]:
        for instructor in section.instructors.all():
            instructors.add(instructor.name)
    if instructors:
        text_parts.extend(list(instructors))
    
    return " ".join(text_parts)

def populate_via_docker_exec(courses, limit, batch_size):
    """Populate using Docker exec (works when local PostgreSQL conflicts)"""
    import subprocess
    
    print("Using Docker exec method...")
    total = 0
    start = time.time()
    
    for i in range(0, len(courses), batch_size):
        batch = courses[i:i+batch_size]
        batch_num = i // batch_size + 1
        
        texts = []
        data = []
        for course in batch:
            text = create_course_text(course)
            if text.strip():
                texts.append(text)
                data.append({
                    'code': course.full_code,
                    'text': text,
                    'url': f"/course/{course.full_code}/{course.semester}"
                })
        
        if not texts:
            continue
        
        print(f"Batch {batch_num}: Embedding {len(texts)}...", end=" ")
        try:
            response = client.embeddings.create(model="text-embedding-3-small", input=texts)
            embeddings = [item.embedding for item in response.data]
        except Exception as e:
            print(f"ERROR: {e}")
            continue
        
        print("Inserting...", end=" ")
        values = []
        for d, emb in zip(data, embeddings):
            emb_str = "[" + ",".join(map(str, emb)) + "]"
            code_esc = d['code'].replace("'", "''")
            text_esc = d['text'].replace("'", "''").replace("\\", "\\\\")
            url_esc = d['url'].replace("'", "''")
            
            values.append(f"('{code_esc}', '{text_esc}', '{url_esc}', '{emb_str}'::vector, CURRENT_TIMESTAMP)")
        
        bulk_sql = f"""INSERT INTO course_documents (course_code, text, url, embedding, updated_at)
VALUES {', '.join(values)}
ON CONFLICT (course_code) DO UPDATE SET
    text = EXCLUDED.text, url = EXCLUDED.url,
    embedding = EXCLUDED.embedding, updated_at = CURRENT_TIMESTAMP;"""
        
        result = subprocess.run(
            ["docker", "exec", "-i", "backend-db-1", "psql", "-U", "penn-courses", "-d", "postgres", "-q"],
            input=bulk_sql,
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            total += len(data)
        else:
            print(f"\n⚠ Insert error: {result.stderr[:100]}")
        
        elapsed = time.time() - start
        rate = total / elapsed if elapsed > 0 else 0
        print(f"✓ {total} total ({rate:.1f}/sec)")
    
    result = subprocess.run(
        ["docker", "exec", "-i", "backend-db-1", "psql", "-U", "penn-courses", "-d", "postgres", "-t", "-A", "-c", "SELECT COUNT(*) FROM course_documents WHERE embedding IS NOT NULL;"],
        capture_output=True,
        text=True
    )
    final_count = result.stdout.strip()
    
    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)
    print(f"Total processed: {total}")
    print(f"Total in database: {final_count}")
    print("="*70)

def populate(limit=None, batch_size=200):
    """Populate pgvector table"""
    print("="*70)
    print("Populating pgvector with course embeddings")
    print("="*70)
    
    courses_qs = Course.objects.filter(course_filters_pcr).select_related('department')
    if limit:
        courses_qs = courses_qs[:limit]
    
    courses = list(courses_qs)
    total_courses = len(courses)
    print(f"\nProcessing ALL {total_courses:,} courses...")
    print("(Regenerating embeddings for all courses, including existing ones)\n")
    
    
    try:
        conn = psycopg2.connect(
            host="localhost",
            port=5432,
            database="postgres",
            user="penn-courses",
            password="postgres",
            connect_timeout=2
        )
        # Test if we're on the right database
        cur_test = conn.cursor()
        cur_test.execute("SELECT tablename FROM pg_tables WHERE tablename='course_documents' AND schemaname='public'")
        if not cur_test.fetchone():
            conn.close()
            raise Exception("Table not found - wrong database")
        cur_test.close()
    except Exception as e:
        print(f"\n⚠ Direct connection issue: {e}")
        print("Using Docker exec method instead...")
        return populate_via_docker_exec(courses, limit, batch_size)
    cur = conn.cursor()
    
    total = 0
    start = time.time()
    
    for i in range(0, len(courses), batch_size):
        batch = courses[i:i+batch_size]
        batch_num = i // batch_size + 1
        total_batches = (len(courses) + batch_size - 1) // batch_size
        
        print(f"Batch {batch_num}/{total_batches}: Processing {len(batch)} courses...", end=" ")
        
        texts = []
        data = []
        for course in batch:
            text = create_course_text(course)
            if text.strip():
                texts.append(text)
                data.append({
                    'code': course.full_code,
                    'text': text,
                    'url': f"/course/{course.full_code}/{course.semester}"
                })
        
        if not texts:
            print("No valid texts, skipping")
            continue
        
        # Generate embeddings
        try:
            response = client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            embeddings = [item.embedding for item in response.data]
        except Exception as e:
            print(f"ERROR embedding: {e}")
            continue
        
        inserted = 0
        for d, emb in zip(data, embeddings):
            emb_str = "[" + ",".join(map(str, emb)) + "]"
            try:
                cur.execute("""
                    INSERT INTO course_documents (course_code, text, url, embedding, updated_at)
                    VALUES (%s, %s, %s, %s::vector, CURRENT_TIMESTAMP)
                    ON CONFLICT (course_code) DO UPDATE SET
                        text = EXCLUDED.text,
                        url = EXCLUDED.url,
                        embedding = EXCLUDED.embedding,
                        updated_at = CURRENT_TIMESTAMP
                """, [d['code'], d['text'], d['url'], emb_str])
                inserted += 1
                total += 1
            except Exception as e:
                if "does not exist" in str(e).lower():
                    print(f"\n❌ ERROR: course_documents table doesn't exist!")
                    print("Run: docker exec -i backend-db-1 psql -U penn-courses -d postgres < setup_pgvector.sql")
                    cur.close()
                    conn.close()
                    return
                else:
                    print(f"\n⚠ Error inserting {d['code']}: {e}")
        
        conn.commit()
        
        elapsed = time.time() - start
        rate = total / elapsed if elapsed > 0 else 0
        print(f"✓ {inserted} inserted ({total} total, {rate:.1f}/sec)")
    
    # Final stats
    cur.execute("SELECT COUNT(*) FROM course_documents WHERE embedding IS NOT NULL")
    final_count = cur.fetchone()[0]
    
    cur.close()
    conn.close()
    
    elapsed_total = time.time() - start
    print("\n" + "="*70)
    print("COMPLETE!")
    print("="*70)
    print(f"Total processed: {total}")
    print(f"Total in database: {final_count}")
    print(f"Time: {elapsed_total/60:.2f} minutes")
    print(f"Rate: {total/elapsed_total:.2f} courses/second")
    print("="*70)

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--limit', type=int, help='Limit number of courses (for testing)')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size')
    args = parser.parse_args()
    
    populate(limit=args.limit, batch_size=args.batch_size)

