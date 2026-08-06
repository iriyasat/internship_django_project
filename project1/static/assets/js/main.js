(function() {
  "use strict";
  const select = (el, all = false) => {
    el = el.trim()
    if (all) {
      return [...document.querySelectorAll(el)]
    } else {
      return document.querySelector(el)
    }
  }
  const on = (type, el, listener, all = false) => {
    if (all) {
      select(el, all).forEach(e => e.addEventListener(type, listener))
    } else {
      select(el, all).addEventListener(type, listener)
    }
  }
  const onscroll = (el, listener) => {
    el.addEventListener('scroll', listener)
  }
  if (select('.toggle-sidebar-btn')) {
    on('click', '.toggle-sidebar-btn', function(e) {
      select('body').classList.toggle('toggle-sidebar')
    })
  }
  if (select('.search-bar-toggle')) {
    on('click', '.search-bar-toggle', function(e) {
      select('.search-bar').classList.toggle('search-bar-show')
    })
  }
  let navbarlinks = select('#navbar .scrollto', true)
  const navbarlinksActive = () => {
    let position = window.scrollY + 200
    navbarlinks.forEach(navbarlink => {
      if (!navbarlink.hash) return
      let section = select(navbarlink.hash)
      if (!section) return
      if (position >= section.offsetTop && position <= (section.offsetTop + section.offsetHeight)) {
        navbarlink.classList.add('active')
      } else {
        navbarlink.classList.remove('active')
      }
    })
  }
  window.addEventListener('load', navbarlinksActive)
  onscroll(document, navbarlinksActive)
  let selectHeader = select('#header')
  if (selectHeader) {
    const headerScrolled = () => {
      if (window.scrollY > 100) {
        selectHeader.classList.add('header-scrolled')
      } else {
        selectHeader.classList.remove('header-scrolled')
      }
    }
    window.addEventListener('load', headerScrolled)
    onscroll(document, headerScrolled)
  }
  let backtotop = select('.back-to-top')
  if (backtotop) {
    const toggleBacktotop = () => {
      if (window.scrollY > 100) {
        backtotop.classList.add('active')
      } else {
        backtotop.classList.remove('active')
      }
    }
    window.addEventListener('load', toggleBacktotop)
    onscroll(document, toggleBacktotop)
  }
  var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'))
  var tooltipList = tooltipTriggerList.map(function(tooltipTriggerEl) {
    return new bootstrap.Tooltip(tooltipTriggerEl)
  })
  if (select('.quill-editor-default')) {
    new Quill('.quill-editor-default', {
      theme: 'snow'
    });
  }
  if (select('.quill-editor-bubble')) {
    new Quill('.quill-editor-bubble', {
      theme: 'bubble'
    });
  }
  if (select('.quill-editor-full')) {
    new Quill(".quill-editor-full", {
      modules: {
        toolbar: [
          [{
            font: []
          }, {
            size: []
          }],
          ["bold", "italic", "underline", "strike"],
          [{
              color: []
            },
            {
              background: []
            }
          ],
          [{
              script: "super"
            },
            {
              script: "sub"
            }
          ],
          [{
              list: "ordered"
            },
            {
              list: "bullet"
            },
            {
              indent: "-1"
            },
            {
              indent: "+1"
            }
          ],
          ["direction", {
            align: []
          }],
          ["link", "image", "video"],
          ["clean"]
        ]
      },
      theme: "snow"
    });
  }
  if (typeof tinymce !== 'undefined') {
    const useDarkMode = window.matchMedia('(prefers-color-scheme: dark)').matches;
    const isSmallScreen = window.matchMedia('(max-width: 1023.5px)').matches;
    tinymce.init({
      selector: 'textarea.tinymce-editor',
      plugins: 'preview importcss searchreplace autolink autosave save directionality code visualblocks visualchars fullscreen image link media template codesample table charmap pagebreak nonbreaking anchor insertdatetime advlist lists wordcount help charmap quickbars emoticons',
      editimage_cors_hosts: ['picsum.photos'],
      menubar: 'file edit view insert format tools table help',
      toolbar: 'undo redo | bold italic underline strikethrough | fontfamily fontsize blocks | alignleft aligncenter alignright alignjustify | outdent indent |  numlist bullist | forecolor backcolor removeformat | pagebreak | charmap emoticons | fullscreen  preview save print | insertfile image media template link anchor codesample | ltr rtl',
      toolbar_sticky: true,
      toolbar_sticky_offset: isSmallScreen ? 102 : 108,
      autosave_ask_before_unload: true,
      autosave_interval: '30s',
      autosave_prefix: '{path}{query}-{id}-',
      autosave_restore_when_empty: false,
      autosave_retention: '2m',
      image_advtab: true,
      link_list: [{
          title: 'My page 1',
          value: 'https://www.tiny.cloud'
        },
        {
          title: 'My page 2',
          value: 'http://www.moxiecode.com'
        }
      ],
      image_list: [{
          title: 'My page 1',
          value: 'https://www.tiny.cloud'
        },
        {
          title: 'My page 2',
          value: 'http://www.moxiecode.com'
        }
      ],
      image_class_list: [{
          title: 'None',
          value: ''
        },
        {
          title: 'Some class',
          value: 'class-name'
        }
      ],
      importcss_append: true,
      file_picker_callback: (callback, value, meta) => {
        if (meta.filetype === 'file') {
          callback('https://www.google.com/logos/google.jpg', {
            text: 'My text'
          });
        }
        if (meta.filetype === 'image') {
          callback('https://www.google.com/logos/google.jpg', {
            alt: 'My alt text'
          });
        }
        if (meta.filetype === 'media') {
          callback('movie.mp4', {
            source2: 'alt.ogg',
            poster: 'https://www.google.com/logos/google.jpg'
          });
        }
      },
      templates: [{
          title: 'New Table',
          description: 'creates a new table',
          content: '<div class="mceTmpl"><table width="98%%"  border="0" cellspacing="0" cellpadding="0"><tr><th scope="col"> </th><th scope="col"> </th></tr><tr><td> </td><td> </td></tr></table></div>'
        },
        {
          title: 'Starting my story',
          description: 'A cure for writers block',
          content: 'Once upon a time...'
        },
        {
          title: 'New list with dates',
          description: 'New List with dates',
          content: '<div class="mceTmpl"><span class="cdate">cdate</span><br><span class="mdate">mdate</span><h2>My List</h2><ul><li></li><li></li></ul></div>'
        }
      ],
      template_cdate_format: '[Date Created (CDATE): %m/%d/%Y : %H:%M:%S]',
      template_mdate_format: '[Date Modified (MDATE): %m/%d/%Y : %H:%M:%S]',
      height: 600,
      image_caption: true,
      quickbars_selection_toolbar: 'bold italic | quicklink h2 h3 blockquote quickimage quicktable',
      noneditable_class: 'mceNonEditable',
      toolbar_mode: 'sliding',
      contextmenu: 'link image table',
      skin: useDarkMode ? 'oxide-dark' : 'oxide',
      content_css: useDarkMode ? 'dark' : 'default',
      content_style: 'body { font-family:Helvetica,Arial,sans-serif; font-size:16px }'
    });
  }
  var needsValidation = document.querySelectorAll('.needs-validation')
  Array.prototype.slice.call(needsValidation)
    .forEach(function(form) {
      form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
          event.preventDefault()
          event.stopPropagation()
        }
        form.classList.add('was-validated')
      }, false)
    })
  const datatables = select('.datatable', true)
  datatables.forEach(datatable => {
    new simpleDatatables.DataTable(datatable, {
      perPageSelect: [5, 10, 15, ["All", -1]],
      columns: [{
          select: 2,
          sortSequence: ["desc", "asc"]
        },
        {
          select: 3,
          sortSequence: ["desc"]
        },
        {
          select: 4,
          cellClass: "green",
          headerClass: "red"
        }
      ]
    });
  })
  const mainContainer = select('#main');
  if (mainContainer) {
    setTimeout(() => {
      new ResizeObserver(function() {
        select('.echart', true).forEach(getEchart => {
          echarts.getInstanceByDom(getEchart).resize();
        })
      }).observe(mainContainer);
    }, 200);
  }
  window.pdfStyles = {
    primary: [79, 70, 229],      
    textDark: [30, 41, 59],      
    textMuted: [100, 116, 139],  
    bgLight: [248, 250, 252],   
    borderColor: [226, 232, 240], 
    headStyles: {
      fillColor: [79, 70, 229],
      textColor: [255, 255, 255],
      fontStyle: 'bold'
    },
    bodyStyles: {
      textColor: [30, 41, 59],
      font: 'helvetica'
    }
  };
  function getCellValue(row, index) {
    const cell = row.cells[index];
    if (!cell) return '';
    return (cell.innerText || cell.textContent).trim();
  }
  function cleanNumericValue(val) {
    let clean = val.replace(/[\$,%]/g, '').trim();
    if (clean.startsWith('(') && clean.endsWith(')')) {
      clean = '-' + clean.substring(1, clean.length - 1);
    }
    return clean;
  }
  function parseValue(val) {
    if (!val) return '';
    const clean = cleanNumericValue(val);
    const num = Number(clean);
    if (clean !== '' && !isNaN(num)) {
      return num;
    }
    if (val.length > 5 && (val.includes('-') || val.includes('/') || /[a-zA-Z]/.test(val))) {
      const parsedDate = Date.parse(val);
      if (!isNaN(parsedDate)) {
        return parsedDate;
      }
    }
    return val.toLowerCase();
  }
  function sortTableColumn(table, colIndex, asc) {
    const tbody = table.querySelector('tbody');
    if (!tbody) return;
    const rows = Array.from(tbody.querySelectorAll('tr'));
    if (rows.length === 0) return;
    if (rows.length === 1 && rows[0].querySelector('td[colspan]')) return;
    rows.sort((rowA, rowB) => {
      const valA = getCellValue(rowA, colIndex);
      const valB = getCellValue(rowB, colIndex);
      const isSpecialA = valA === '' || valA.toLowerCase() === 'n/a';
      const isSpecialB = valB === '' || valB.toLowerCase() === 'n/a';
      if (isSpecialA && !isSpecialB) return 1;
      if (!isSpecialA && isSpecialB) return -1;
      if (isSpecialA && isSpecialB) return 0;
      const parsedA = parseValue(valA);
      const parsedB = parseValue(valB);
      if (typeof parsedA === 'number' && typeof parsedB === 'number') {
        return asc ? parsedA - parsedB : parsedB - parsedA;
      }
      const strA = String(parsedA);
      const strB = String(parsedB);
      return asc 
        ? strA.localeCompare(strB, undefined, { numeric: true, sensitivity: 'base' })
        : strB.localeCompare(strA, undefined, { numeric: true, sensitivity: 'base' });
    });
    rows.forEach(row => tbody.appendChild(row));
  }
  function initSingleTable(table) {
    if (table._dtccInitialized) return;
    table._dtccInitialized = true;
    const thead = table.querySelector('thead');
    if (!thead) return;
    const headers = thead.querySelectorAll('tr:last-child th');
    headers.forEach((th, colIndex) => {
      const headerText = th.textContent.trim().toLowerCase();
      if (headerText === 'actions' || headerText === 'action' || th.classList.contains('no-sort')) {
        return;
      }
      if (th.querySelector('.dtcc')) return;
      th.style.position = 'relative';
      th.style.cursor = 'pointer';
      const dtccSpan = document.createElement('span');
      dtccSpan.className = 'dtcc';
      dtccSpan.innerHTML = `
        <button class="dtcc-button dtcc-button_order" type="button" aria-label="Toggle ordering" title="Sort Column">
          <span class="dtcc-button-icon">
            <svg xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
              <path d="m3 8 4-4 4 4"></path>
              <path d="m11 16-4 4-4-4"></path>
              <path d="M7 4v16"></path>
              <path d="M15 8h6"></path>
              <path d="M15 16h6"></path>
              <path d="M13 12h8"></path>
            </svg>
          </span>
          <span class="dtcc-button-text">Toggle ordering</span>
          <span class="dtcc-button-state"></span>
          <span class="dtcc-button-extra"></span>
        </button>
      `;
      th.appendChild(dtccSpan);
      let sortAsc = true;
      const orderBtn = dtccSpan.querySelector('.dtcc-button_order');
      function triggerSort(asc) {
        sortTableColumn(table, colIndex, asc);
        thead.querySelectorAll('.dtcc-button_order').forEach(btn => {
          btn.classList.remove('dtcc-button_active', 'dtcc-button_desc');
        });
        orderBtn.classList.add('dtcc-button_active');
        if (!asc) {
          orderBtn.classList.add('dtcc-button_desc');
        }
      }
      orderBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        triggerSort(sortAsc);
        sortAsc = !sortAsc;
      });
      th.addEventListener('click', (e) => {
        if (e.target.closest('button')) {
          return;
        }
        orderBtn.click();
      });
    });
  }
  function initTableSorting() {
    const tables = document.querySelectorAll('table.table:not(.datatable)');
    tables.forEach(table => initSingleTable(table));
  }
  function observeDynamicTables() {
    const main = document.getElementById('main') || document.body;
    const observer = new MutationObserver((mutations) => {
      mutations.forEach(mutation => {
        mutation.addedNodes.forEach(node => {
          if (node.nodeType !== Node.ELEMENT_NODE) return;
          if (node.matches && node.matches('table.table:not(.datatable)')) {
            initSingleTable(node);
          }
          if (node.querySelectorAll) {
            const tables = node.querySelectorAll('table.table:not(.datatable)');
            tables.forEach(table => initSingleTable(table));
          }
        });
      });
    });
    observer.observe(main, { childList: true, subtree: true });
  }
  initTableSorting();
  observeDynamicTables();
})();
