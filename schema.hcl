schema "demo" {
  charset   = "utf8mb4"
  collation = "utf8mb4_unicode_ci"
}

table "users" {
  schema = schema.demo

  column "id" {
    type           = int
    auto_increment = true
  }
  column "name" {
    type = varchar(100)
    null = false
  }
  column "email" {
    type = varchar(255)
    null = false
  }
  column "created_at" {
    type    = timestamp
    null    = false
    default = sql("CURRENT_TIMESTAMP")
  }

  primary_key {
    columns = [column.id]
  }
  index "idx_email" {
    unique  = true
    columns = [column.email]
  }
}

table "tasks" {
  schema = schema.demo

  column "id" {
    type           = int
    auto_increment = true
  }
  column "user_id" {
    type = int
    null = false
  }
  column "title" {
    type = varchar(255)
    null = false
  }
  column "done" {
    type    = boolean
    null    = false
    default = false
  }
  column "created_at" {
    type    = timestamp
    null    = false
    default = sql("CURRENT_TIMESTAMP")
  }

  primary_key {
    columns = [column.id]
  }
  foreign_key "fk_user" {
    columns     = [column.user_id]
    ref_columns = [table.users.column.id]
    on_delete   = CASCADE
  }
  index "idx_user" {
    columns = [column.user_id]
  }
}
