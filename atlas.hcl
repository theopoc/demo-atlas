
# Env pour Atlas via Docker (dans le réseau Compose)
env "docker" {
  src = "file://schema.hcl"
  url = "mysql://root:password@demo-atlas-mysql:3306/demo"
  dev = "mysql://root:password@demo-atlas-mysql:3306/atlas_dev"
  migration {
    dir = "file://migrations"
  }
}
