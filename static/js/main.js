document.addEventListener('DOMContentLoaded', function() {
    
    // Function to handle Non-Training Activity checkbox
    function attachCheckboxListener(checkbox, row) {
        checkbox.addEventListener('change', function() {
            const isChecked = this.checked;
            const hiddenInput = row.querySelector('.is-training-hidden');
            hiddenInput.value = isChecked ? 'false' : 'true';
            
            const trainingFields = row.querySelectorAll('.training-field');
            trainingFields.forEach(field => {
                if (isChecked) {
                    field.style.display = 'none';
                    // Remove required attribute from inputs within
                    field.querySelectorAll('input, select').forEach(input => input.removeAttribute('required'));
                } else {
                    field.style.display = 'block';
                    // Add required attribute
                    field.querySelectorAll('input, select').forEach(input => input.setAttribute('required', 'required'));
                }
            });
        });
    }

    // Initialize for the first row if present
    const firstRow = document.querySelector('.entry-row');
    if (firstRow) {
        const firstCheckbox = firstRow.querySelector('.is-training-cb');
        
        if (firstCheckbox) {
            attachCheckboxListener(firstCheckbox, firstRow);
        }
    }

    // Add Row functionality
    const addRowBtn = document.getElementById('add-row-btn');
    const entriesContainer = document.getElementById('entries-container');

    if (addRowBtn && entriesContainer) {
        addRowBtn.addEventListener('click', function() {
            // Clone the first row
            const firstRow = entriesContainer.querySelector('.entry-row');
            const newRow = firstRow.cloneNode(true);
            
            // Clear inputs in the new row
            const inputs = newRow.querySelectorAll('input[type="text"], input[type="number"], select, textarea');
            inputs.forEach(input => {
                input.value = '';
            });
            
            // Reset checkbox and hidden field
            const cb = newRow.querySelector('.is-training-cb');
            if (cb) {
                cb.checked = false;
                newRow.querySelector('.is-training-hidden').value = 'true';
            }
            
            // Reset visibility of training fields
            newRow.querySelectorAll('.training-field').forEach(field => {
                field.style.display = 'block';
                field.querySelectorAll('input, select').forEach(input => input.setAttribute('required', 'required'));
            });
            
            // Remove row button functionality
            const removeBtnDiv = newRow.querySelector('.remove-btn-container');
            if (!removeBtnDiv) {
                // If the original didn't have a remove button, add it
                const div = document.createElement('div');
                div.className = 'form-group remove-btn-container';
                div.innerHTML = `<button type="button" class="btn btn-danger btn-sm remove-row-btn">Remove</button>`;
                newRow.appendChild(div);
            } else {
                removeBtnDiv.innerHTML = `<button type="button" class="btn btn-danger btn-sm remove-row-btn">Remove</button>`;
            }

            // Attach change listeners to the new row
            const newCheckbox = newRow.querySelector('.is-training-cb');
            
            if (newCheckbox) attachCheckboxListener(newCheckbox, newRow);

            entriesContainer.appendChild(newRow);
        });

        // Event delegation for dynamically added remove buttons
        entriesContainer.addEventListener('click', function(e) {
            if (e.target && e.target.classList.contains('remove-row-btn')) {
                const row = e.target.closest('.entry-row');
                if (entriesContainer.querySelectorAll('.entry-row').length > 1) {
                    row.remove();
                } else {
                    alert('You must have at least one entry row.');
                }
            }
        });
    }
});
