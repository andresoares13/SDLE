const createListButton = document.getElementById('createListButton');
    const addListForm = document.getElementById('addListForm');

    createListButton.addEventListener('click', () => {
        if (addListForm.style.display === 'none' || addListForm.style.display === '') {
            addListForm.style.display = 'block';
        } else {
            addListForm.style.display = 'none';
        }
    });
    
const addExistingListButton = document.getElementById('addExistingListButton');
    const addExistingListForm = document.getElementById('addExistingListForm');

    addExistingListButton.addEventListener('click', () => {
        if (addExistingListForm.style.display === 'none' || addExistingListForm.style.display === '') {
            addExistingListForm.style.display = 'block';
        } else {
            addExistingListForm.style.display = 'none';
        }
    });
    
    

    
    

