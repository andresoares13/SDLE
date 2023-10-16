const createListButton = document.getElementById('createListButton');
    const addListForm = document.getElementById('addListForm');

    createListButton.addEventListener('click', () => {
        if (addListForm.style.display === 'none' || addListForm.style.display === '') {
            addListForm.style.display = 'block';
        } else {
            addListForm.style.display = 'none';
        }
    });
