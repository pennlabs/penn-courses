#!/bin/bash

# Define the list of products
products=("review" "plan" "alert" "landing" "backend" "nginx")

# Loop over each product
for product in "${products[@]}"; do
    echo "Deploying Fly app for $product"

    # Check if the product is 'backend'
    if [ "$product" == "backend" ]; then
        flyctl deploy -a penn-course-$product --ha=false --remote-only --config config/fly/$product.toml --dockerfile backend/Dockerfile
    else 
        if [ "$product" == "nginx" ]; then
            flyctl deploy -a penn-course-$product --ha=false --remote-only --config config/fly/nginx/fly.toml --dockerfile config/fly/nginx/Dockerfile
        else
            flyctl deploy -a penn-course-$product --ha=false --remote-only --config config/fly/$product.toml --dockerfile frontend/$product/Dockerfile
        fi
    fi

    # Update the image
    flyctl image update -a penn-course-$product -y
done
