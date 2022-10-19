// This file controls the functionality of the 'Create new gallery' input and
// the photo update forms

function newGalleryInput(selector, div) {
    let text = `
        <input class="form-control mb-1"
        type='text'
        id='gallery_create'
        name='gallery_create'
        autocomplete='off'
        placeholder='Create new gallery'
        required/>
        `.trim();
    
    // this *if* statement primes the browser to automatically create new gallery input
    // if the "create new gallery" option happened to be selected upon page reload
    if (selector.value === "create new gallery") {
        div.innerHTML = text;
    }
    else {
        div.innerHTML = "";
    }

    // this .onchange call creates a new gallery input upon selecting "create new gallery"
    selector.onchange = (e) => {
        if (selector.value === "create new gallery") {
            div.innerHTML = text;
        }
        else {
            div.innerHTML = "";
        }
    }
}

const mainFormSelect = document.querySelector("#gallery");
const mainFormDiv = document.getElementById("new_gallery");

newGalleryInput(mainFormSelect, mainFormDiv);

// this script controls the 'update' buttons next to each image
const update_buttons = document.querySelectorAll(".update");
update_buttons.forEach(function(button) {
    button.onclick = function() {
        if (window.matchMedia("(max-width: 800px)").matches) {
            alert("Please update photo entries on desktop.");
        }
        else if (window.matchMedia("(max-height: 700px)").matches) {
            alert("Please update photo entries on desktop.");
        }
        else {
            let id = this.id
            // id = 'update-image-{{ photo['id'] }}'

            id = id.replace('update-image-', '');
            // id = '{{ photo['id'] }}'

            updateForm = document.getElementById("update-form-" + id);
            updateForm.classList.toggle("d-none");

            let select = document.getElementById("update-gallery-" + id);
            let div = document.getElementById("new-gallery-" + id);

            newGalleryInput(select, div);
        }
    }
});