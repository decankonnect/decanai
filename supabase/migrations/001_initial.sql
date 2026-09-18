create extension if not exists vector;
create extension if not exists pgcrypto;

create table if not exists sessions (id uuid primary key default gen_random_uuid(), session_token uuid unique not null, created_at timestamptz not null default now(), last_active_at timestamptz not null default now(), metadata jsonb not null default '{}'::jsonb);
create table if not exists conversations (id uuid primary key default gen_random_uuid(), session_id uuid not null references sessions(id) on delete cascade, title text not null default 'New conversation', created_at timestamptz not null default now(), updated_at timestamptz not null default now(), archived boolean not null default false);
create table if not exists messages (id uuid primary key default gen_random_uuid(), conversation_id uuid not null references conversations(id) on delete cascade, role text not null check (role in ('user','assistant','system')), content text not null, model text, token_count integer, created_at timestamptz not null default now(), metadata jsonb not null default '{}'::jsonb);
create table if not exists knowledge_documents (id uuid primary key default gen_random_uuid(), session_id uuid not null references sessions(id) on delete cascade, title text not null, file_name text, file_type text not null, storage_path text, extracted_text text, status text not null default 'uploading' check (status in ('uploading','processing','ready','failed')), created_at timestamptz not null default now(), updated_at timestamptz not null default now(), metadata jsonb not null default '{}'::jsonb);
create table if not exists training_entries (id uuid primary key default gen_random_uuid(), session_id uuid not null references sessions(id) on delete cascade, title text not null, content text not null, source text, category text, created_at timestamptz not null default now(), updated_at timestamptz not null default now(), metadata jsonb not null default '{}'::jsonb);
create table if not exists knowledge_chunks (id uuid primary key default gen_random_uuid(), document_id uuid references knowledge_documents(id) on delete cascade, training_entry_id uuid references training_entries(id) on delete cascade, session_id uuid not null references sessions(id) on delete cascade, chunk_index integer not null, content text not null, embedding vector(1536) not null, metadata jsonb not null default '{}'::jsonb, created_at timestamptz not null default now());
create table if not exists image_inputs (id uuid primary key default gen_random_uuid(), session_id uuid not null references sessions(id) on delete cascade, conversation_id uuid references conversations(id) on delete set null, storage_path text not null, mime_type text not null, analysis text, created_at timestamptz not null default now(), metadata jsonb not null default '{}'::jsonb);
create table if not exists feedback (id uuid primary key default gen_random_uuid(), session_id uuid not null references sessions(id) on delete cascade, message_id uuid references messages(id) on delete cascade, rating smallint check (rating in (-1,1)), feedback_text text, created_at timestamptz not null default now());
create index if not exists conversations_session_idx on conversations(session_id, updated_at desc);
create index if not exists messages_conversation_idx on messages(conversation_id, created_at);
create index if not exists knowledge_chunks_session_idx on knowledge_chunks(session_id);
create index if not exists knowledge_chunks_embedding_idx on knowledge_chunks using ivfflat (embedding vector_cosine_ops) with (lists = 100);

create or replace function match_knowledge_chunks(query_embedding vector(1536), match_threshold float, match_count int, p_session_id uuid)
returns table(id uuid, content text, metadata jsonb, similarity float)
language sql stable security definer set search_path = public as $$
  select knowledge_chunks.id, knowledge_chunks.content, knowledge_chunks.metadata, 1 - (knowledge_chunks.embedding <=> query_embedding) as similarity
  from knowledge_chunks
  where knowledge_chunks.session_id = p_session_id and 1 - (knowledge_chunks.embedding <=> query_embedding) >= match_threshold
  order by knowledge_chunks.embedding <=> query_embedding limit match_count;
$$;

alter table sessions enable row level security;
alter table conversations enable row level security;
alter table messages enable row level security;
alter table knowledge_documents enable row level security;
alter table training_entries enable row level security;
alter table knowledge_chunks enable row level security;
alter table image_inputs enable row level security;
alter table feedback enable row level security;

insert into storage.buckets (id, name, public) values ('decan-documents','decan-documents',false), ('decan-images','decan-images',false) on conflict (id) do nothing;
