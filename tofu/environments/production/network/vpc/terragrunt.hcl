include "root" {
  path   = find_in_parent_folders()
  expose = true
}

include "environment" {
  path   = find_in_parent_folders("environment.hcl")
  expose = true
}

terraform {
  source = "../../../../modules/network/vpc"
}

locals {
  environment = include.environment.locals.environment
  name_prefix = "tb-${include.root.locals.short_name}-${include.environment.locals.environment}"
  region      = include.environment.locals.region

  project_tags     = include.root.locals.tags
  environment_tags = include.environment.locals.tags
  tags             = "${merge(local.project_tags, local.environment_tags)}"
}

inputs = {
  environment = local.environment
  name_prefix = local.name_prefix
  region      = local.region
  vpc_cidr    = "10.0.0.0/16"
  tags        = local.tags
}