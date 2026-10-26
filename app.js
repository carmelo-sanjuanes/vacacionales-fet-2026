// Asignaturas por Semestre (transcritas fielmente de la imagen provista)
const SUBJECTS = [
    // Semestre 7
    { code: 'ELE0300218', name: 'ECUACIONES DIFERENCIALES', semester: 7 },
    { code: 'ELE0300735', name: 'SEÑALES Y CONTROL', semester: 7 },
    { code: 'ELE0300736', name: 'ELECTRÓNICA II TP', semester: 7 },
    { code: 'ELE0300730', name: 'SISTEMAS DE DISTRIBUCIÓN DE ENERGÍA', semester: 7 },
    { code: 'ELE0300731', name: 'CIRCUITOS ELÉCTRICOS III', semester: 7 },
    { code: 'ELE0300732', name: 'AUTOMATIZACIÓN', semester: 7 },
    { code: 'ELE0300733', name: 'MÁQUINAS ELÉCTRICAS II TP', semester: 7 },
    { code: 'ELE0300734', name: 'OPERACIONES Y MANTENIMIENTO I', semester: 7 },

    // Semestre 8
    { code: 'ELE0300219', name: 'MATEMÁTICAS DISCRETAS', semester: 8 },
    { code: 'ELE0300220', name: 'SIMULACIÓN TP', semester: 8 },
    { code: 'ELE0300223', name: 'ESTADÍSTICA Y PROBABILIDAD', semester: 8 },
    { code: 'ELE0300737', name: 'MECÁNICA DE FLUIDOS', semester: 8 },
    { code: 'ELE0300738', name: 'SISTEMAS DE TRANSMISIÓN DE ENERGÍA', semester: 8 },
    { code: 'ELE0300739', name: 'SUBESTACIONES ELÉCTRICAS', semester: 8 },
    { code: 'ELE0300208', name: 'PLANEACIÓN ENERGÉTICA', semester: 8 },
    { code: 'ELE0300217', name: 'OPTATIVA PROFESIONAL I', semester: 8 },
    { code: 'ELE0300741', name: 'FORMULACIÓN Y EVALUACIÓN DE PROYECTOS', semester: 8 },

    // Semestre 9
    { code: 'ELE0300221', name: 'MÉTODOS NUMÉRICOS', semester: 9 },
    { code: 'ELE0300742', name: 'ANÁLISIS DE SISTEMAS DE POTENCIA', semester: 9 },
    { code: 'ELE0300743', name: 'OPERACIONES Y MANTENIMIENTO II', semester: 9 },
    { code: 'ELE0300744', name: 'GENERACIÓN HIDRAULICA', semester: 9 },
    { code: 'ELE0300745', name: 'GENERACIÓN TÉRMICA', semester: 9 },
    { code: 'ELE0300747', name: 'OPTATIVA PROFESIONAL II', semester: 9 },
    { code: 'ELE0300837', name: 'ÉTICA PROFESIONAL', semester: 9 },
    { code: 'ELE0300116', name: 'ELECTIVA III - MARKETING PARA EMPRESARIOS', semester: 9 }
];

// Configuración de la App
const MIN_STUDENTS_TO_OPEN = 5; // Cupo recomendado para abrir el curso vacacional
const LOCAL_STORAGE_KEY = 'fet_vacacionales_registrations';
const BACKEND_URL = 'https://script.google.com/macros/s/AKfycbx7zKE41qQi23E7l7yUQNvAT5n80FBnyWD7zV7_fTNzh26eg8kujtZkOeFsf_ulhjgF/exec'; // COLOQUE AQUÍ SU URL DE GOOGLE APPS SCRIPT PARA HABILITAR LA BASE DE DATOS COMPARTIDA

// Estado global de la aplicación
let registrations = [];
let currentFilterSemester = 'all';

// Elementos del DOM
const registrationForm = document.getElementById('registration-form');
const inputName = document.getElementById('student-name');
const inputCode = document.getElementById('student-code');
const inputPhone = document.getElementById('student-phone');
const btnClearForm = document.getElementById('btn-clear-form');
const totalRegistrationsBadge = document.getElementById('total-registrations');
const scoreItemsContainer = document.getElementById('score-items-container');
const studentsTableBody = document.getElementById('students-table-body');
const searchStudentInput = document.getElementById('search-student');
const btnExport = document.getElementById('btn-export');

// Modal Elements
const modal = document.getElementById('student-modal');
const modalSubjectTitle = document.getElementById('modal-subject-title');
const modalSubjectCode = document.getElementById('modal-subject-code');
const modalSubjectCount = document.getElementById('modal-subject-count');
const modalStudentsList = document.getElementById('modal-students-list');
const closeModalBtn = document.querySelector('.close-modal');

// Módulo de Firma Digital (Touch & Mouse)
let formSigPad = null;
let modalSigPad = null;
const modalSignature = document.getElementById('modal-signature');
const btnOpenFastSign = document.getElementById('btn-open-fast-sign');
const btnCloseSigModal = document.getElementById('btn-close-sig-modal');
const btnCancelSigModal = document.getElementById('btn-cancel-sig-modal');
const btnSaveSigModal = document.getElementById('btn-save-sig-modal');
const modalSigStudentSelect = document.getElementById('modal-sig-student-select');
const modalSigSubjectsList = document.getElementById('modal-sig-subjects-list');

// Inicialización de la aplicación
document.addEventListener('DOMContentLoaded', async () => {
    initSignaturePads();
    renderSubjectChecklists();
    setupEventListeners();
    await loadData();
});

// Cargar registros desde servidor o localStorage
async function loadData() {
    loadFromLocalStorage(); // Cargar firmas y registros locales de inmediato

    if (BACKEND_URL) {
        try {
            const response = await fetch(BACKEND_URL);
            if (response.ok) {
                const cloudData = await response.json();
                // Combinar datos de la nube preservando firmas locales
                registrations = cloudData.map(remote => {
                    const local = registrations.find(r => r.code === remote.code);
                    return {
                        ...remote,
                        signature: remote.signature || (local && local.signature ? local.signature : '')
                    };
                });
                updateUI();
                saveToLocalStorage(); // Mantener copia local actualizada
                prefillActiveStudentPreferences();
                
                // Auto-sincronizar firmas locales que falten en la nube
                checkAndSyncPendingSignatures(cloudData);
            }
        } catch (e) {
            console.error("Error obteniendo datos del servidor, usando local.", e);
        }
    }
}

function loadFromLocalStorage() {
    const rawData = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (rawData) {
        try {
            registrations = JSON.parse(rawData);
            updateUI();
            prefillActiveStudentPreferences();
        } catch (e) {
            console.error("Error cargando los datos guardados, reiniciando vacío.", e);
            registrations = [];
        }
    }
}

// Auto-rellenar preferencias si ya se registró antes en este dispositivo
function prefillActiveStudentPreferences() {
    const activeCode = localStorage.getItem('fet_vacacionales_active_student_code');
    if (!activeCode) return;
    
    const student = registrations.find(r => r.code === activeCode);
    if (student) {
        inputName.value = student.name;
        inputCode.value = student.code;
        inputPhone.value = student.phone;
        
        // Marcar checkboxes
        registrationForm.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.checked = student.subjects.includes(cb.value);
        });

        // Cargar firma guardada si existe
        if (student.signature && formSigPad) {
            formSigPad.loadFromDataURL(student.signature);
        }
        
        showToast(`Tus preferencias y firma han sido cargadas.`, 'success');
    }
}

// Sincronización robusta con Google Sheets (soporta celulares, keepalive y reintentos)
async function syncStudentToCloud(studentData = null, isDelete = false, idToDelete = null) {
    if (!BACKEND_URL) return true;

    const payload = isDelete 
        ? { action: 'delete', id: idToDelete }
        : { action: 'add', student: studentData };

    const bodyStr = JSON.stringify(payload);
    // keepalive está limitado por el navegador a 64KB. Solo usarlo si el payload es menor a 60KB
    const canUseKeepalive = bodyStr.length < 60000;

    let lastError = null;
    for (let attempt = 1; attempt <= 2; attempt++) {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 15000); // 15 seg timeout

            const fetchOptions = {
                method: 'POST',
                body: bodyStr,
                signal: controller.signal
            };
            if (canUseKeepalive) {
                fetchOptions.keepalive = true;
            }

            await fetch(BACKEND_URL, fetchOptions);
            clearTimeout(timeoutId);
            return true;
        } catch (err) {
            lastError = err;
            console.warn(`[Sync] Intento ${attempt} fallido al enviar a la nube:`, err);
            if (attempt < 2) {
                await new Promise(r => setTimeout(r, 800));
            }
        }
    }
    throw lastError || new Error("Error de conexión con la base de datos.");
}

// Guardar registros en localStorage y sincronizar en la nube
async function saveData(studentData = null, isDelete = false, idToDelete = null) {
    saveToLocalStorage();
    
    if (BACKEND_URL) {
        try {
            await syncStudentToCloud(studentData, isDelete, idToDelete);
            
            // Recargar datos desde el servidor para confirmar sincronización
            const response = await fetch(BACKEND_URL);
            if (response.ok) {
                const cloudData = await response.json();
                registrations = cloudData.map(remote => {
                    const local = registrations.find(r => r.code === remote.code);
                    return {
                        ...remote,
                        signature: remote.signature || (local && local.signature ? local.signature : '')
                    };
                });
                updateUI();
                saveToLocalStorage();
                checkAndSyncPendingSignatures(cloudData);
            }
            return true;
        } catch (e) {
            console.error("Error sincronizando con el servidor:", e);
            return false;
        }
    }
    return true;
}

// Auto-sincronizar firmas pendientes (si existen en el celular pero faltan en la nube)
async function checkAndSyncPendingSignatures(cloudData) {
    if (!Array.isArray(cloudData) || !BACKEND_URL) return;
    try {
        const localRaw = localStorage.getItem(LOCAL_STORAGE_KEY);
        if (!localRaw) return;
        const localList = JSON.parse(localRaw);
        
        const pending = localList.filter(loc => {
            if (!loc.signature || String(loc.signature).trim() === '') return false;
            const rem = cloudData.find(c => c.code === loc.code);
            return !rem || !rem.signature || String(rem.signature).trim() === '';
        });

        if (pending.length > 0) {
            console.log(`[Auto-Sync] Se detectaron ${pending.length} firmas guardadas en este equipo no presentes en la nube. Sincronizando...`);
            for (const st of pending) {
                try {
                    await syncStudentToCloud(st, false);
                    console.log(`[Auto-Sync] Firma de ${st.name} sincronizada exitosamente.`);
                } catch(e) {
                    console.warn(`[Auto-Sync] Reintento pendiente para ${st.name}:`, e);
                }
            }
        }
    } catch(err) {
        console.warn("[Auto-Sync] Error verificando firmas pendientes:", err);
    }
}

function saveToLocalStorage() {
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(registrations));
}

// Renderizar las materias con checkboxes en el formulario
function renderSubjectChecklists() {
    const lists = {
        7: document.getElementById('subjects-list-7'),
        8: document.getElementById('subjects-list-8'),
        9: document.getElementById('subjects-list-9')
    };

    // Limpiar listas
    Object.values(lists).forEach(list => list.innerHTML = '');

    SUBJECTS.forEach(subject => {
        const itemHtml = `
            <label class="subject-item-checkbox">
                <input type="checkbox" value="${subject.code}" data-semester="${subject.semester}">
                <div class="checkbox-custom">
                    <i class="fa-solid fa-check"></i>
                </div>
                <div class="subject-info">
                    <span class="subject-code">${subject.code}</span>
                    <span class="subject-name">${subject.name}</span>
                </div>
            </label>
        `;
        
        if (lists[subject.semester]) {
            lists[subject.semester].insertAdjacentHTML('beforeend', itemHtml);
        }
    });
}

// Configurar los listeners de eventos
function setupEventListeners() {
    // Manejo de envío del formulario de registro
    registrationForm.addEventListener('submit', handleFormSubmit);

    // Cambio de Pestañas de Semestre (Formulario)
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            tabButtons.forEach(b => b.classList.remove('active'));
            document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));
            
            btn.classList.add('active');
            const targetSemester = btn.getAttribute('data-semester');
            document.getElementById(`pane-${targetSemester}`).classList.add('active');
        });
    });

    // Filtros del Score de Asignaturas
    const filterButtons = document.querySelectorAll('.filter-btn');
    filterButtons.forEach(btn => {
        btn.addEventListener('click', () => {
            filterButtons.forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentFilterSemester = btn.getAttribute('data-filter');
            renderScores();
        });
    });

    // Barra de búsqueda de estudiantes
    searchStudentInput.addEventListener('input', renderStudentsTable);

    // Botón de exportación
    btnExport.addEventListener('click', exportToCSV);

    // Auto-rellenar preferencias al digitar el código (para otros dispositivos)
    inputCode.addEventListener('input', () => {
        const codeValue = inputCode.value.trim().toUpperCase();
        if (codeValue.length >= 3) {
            const student = registrations.find(r => r.code === codeValue);
            if (student) {
                // Rellenar campos
                inputName.value = student.name;
                inputPhone.value = student.phone;
                
                // Marcar materias
                registrationForm.querySelectorAll('input[type="checkbox"]').forEach(cb => {
                    cb.checked = student.subjects.includes(cb.value);
                });

                // Cargar firma guardada si existe
                if (student.signature && formSigPad) {
                    formSigPad.loadFromDataURL(student.signature);
                }
                
                // Recordar este dispositivo
                localStorage.setItem('fet_vacacionales_active_student_code', student.code);
                showToast(`Cargamos tus preferencias y firma, ${student.name}.`, 'success');
            }
        }
    });

    // Botón Nuevo / Limpiar Formulario
    btnClearForm.addEventListener('click', () => {
        resetForm();
        localStorage.removeItem('fet_vacacionales_active_student_code');
        showToast('Formulario limpio. Puedes ingresar un nuevo registro.', 'info');
    });

    // Cerrar Modal de Asignatura
    closeModalBtn.addEventListener('click', closeModal);
    window.addEventListener('click', (e) => {
        if (e.target === modal) closeModal();
        if (e.target === modalSignature) closeSignatureModal();
    });

    // Módulo de Firma Rápida
    if (btnOpenFastSign) {
        btnOpenFastSign.addEventListener('click', () => openSignatureModal());
    }
    if (btnCloseSigModal) {
        btnCloseSigModal.addEventListener('click', closeSignatureModal);
    }
    if (btnCancelSigModal) {
        btnCancelSigModal.addEventListener('click', closeSignatureModal);
    }
    if (btnSaveSigModal) {
        btnSaveSigModal.addEventListener('click', saveModalSignature);
    }
    if (modalSigStudentSelect) {
        modalSigStudentSelect.addEventListener('change', onModalStudentSelectChange);
    }
}

// Manejar el submit del formulario de registro
async function handleFormSubmit(e) {
    e.preventDefault();

    const name = inputName.value.trim();
    const code = inputCode.value.trim().toUpperCase();
    const phone = inputPhone.value.trim();

    // Obtener las asignaturas seleccionadas de todas las pestañas
    const checkedCheckboxes = Array.from(registrationForm.querySelectorAll('input[type="checkbox"]:checked'));
    
    if (checkedCheckboxes.length === 0) {
        showToast('Debes seleccionar al menos una asignatura de interés.', 'error');
        return;
    }

    const submitBtn = registrationForm.querySelector('button[type="submit"]');
    const origBtnHtml = submitBtn ? submitBtn.innerHTML : '';
    if (submitBtn) {
        submitBtn.disabled = true;
        submitBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Registrando y sincronizando con la nube...';
        submitBtn.style.opacity = '0.9';
    }

    const selectedSubjectCodes = checkedCheckboxes.map(cb => cb.value);

    // Capturar firma si fue dibujada
    const drawnSig = (formSigPad && formSigPad.hasDrawn()) ? formSigPad.toDataURL() : '';

    // Verificar si el estudiante ya está registrado
    const existingIndex = registrations.findIndex(r => r.code === code);
    let targetStudent;
    
    if (existingIndex > -1) {
        // Actualizar registro existente
        registrations[existingIndex].name = name;
        registrations[existingIndex].phone = phone;
        registrations[existingIndex].subjects = selectedSubjectCodes;
        if (drawnSig) {
            registrations[existingIndex].signature = drawnSig;
        }
        targetStudent = registrations[existingIndex];
    } else {
        // Crear nuevo registro
        targetStudent = {
            id: Date.now().toString(),
            name,
            code,
            phone,
            subjects: selectedSubjectCodes,
            date: new Date().toLocaleDateString(),
            signature: drawnSig
        };
        registrations.push(targetStudent);
    }

    // Actualizar interfaz local inmediatamente
    updateUI();

    // Guardar el código en localStorage para recordar este dispositivo
    localStorage.setItem('fet_vacacionales_active_student_code', code);

    // Guardar y sincronizar con la nube
    try {
        const ok = await saveData(targetStudent, false);
        if (ok) {
            showToast(existingIndex > -1 ? '¡Registro y firma actualizados en la nube!' : '¡Estudiante y firma registrados con éxito en la nube!', 'success');
        } else {
            showToast('Guardado en este celular. Se sincronizará con la nube al mejorar la conexión.', 'warning');
        }
    } catch(err) {
        showToast('Guardado en este celular. Se sincronizará automáticamente.', 'warning');
    } finally {
        if (submitBtn) {
            submitBtn.disabled = false;
            submitBtn.innerHTML = origBtnHtml;
            submitBtn.style.opacity = '';
        }
    }
}

// Reiniciar formulario
function resetForm() {
    inputName.value = '';
    inputCode.value = '';
    inputPhone.value = '';
    registrationForm.querySelectorAll('input[type="checkbox"]').forEach(cb => cb.checked = false);
    if (formSigPad) {
        formSigPad.clear();
    }
    
    // Regresar a la primera pestaña (Semestre 7)
    document.querySelectorAll('.tab-btn')[0].click();
}

// Actualizar toda la interfaz de usuario
function updateUI() {
    const totalCount = registrations.length;
    const signedCount = registrations.filter(r => r.signature && String(r.signature).trim() !== '').length;
    const pendingCount = Math.max(0, totalCount - signedCount);
    const percent = totalCount > 0 ? Math.round((signedCount / totalCount) * 100) : 0;

    // Actualizar Banner de Impacto (Hero Stats)
    const elReg = document.getElementById('hero-count-registered');
    if (elReg) elReg.textContent = totalCount;

    const elSig = document.getElementById('hero-count-signed');
    if (elSig) elSig.textContent = signedCount;

    const elPct = document.getElementById('hero-count-percent');
    if (elPct) elPct.textContent = `${percent}%`;

    const elBar = document.getElementById('hero-progress-bar');
    if (elBar) elBar.style.width = `${percent}%`;

    const elPend = document.getElementById('hero-count-pending');
    if (elPend) {
        elPend.innerHTML = `<i class="fa-regular fa-clock"></i> <strong>${pendingCount}</strong> pendientes por firmar`;
    }

    if (totalRegistrationsBadge) {
        totalRegistrationsBadge.textContent = `${totalCount} Estudiantes`;
    }

    renderScores();
    renderStudentsTable();
}

// Renderizar lista de asignaturas y sus scores
function renderScores() {
    scoreItemsContainer.innerHTML = '';

    // Agrupar interés por cada materia
    const subjectScores = SUBJECTS.map(subject => {
        // Encontrar estudiantes interesados
        const interestedStudents = registrations.filter(r => r.subjects.includes(subject.code));
        return {
            ...subject,
            count: interestedStudents.length,
            students: interestedStudents
        };
    });

    // Filtrar por semestre seleccionado
    let filteredScores = subjectScores;
    if (currentFilterSemester !== 'all') {
        const sem = parseInt(currentFilterSemester);
        filteredScores = subjectScores.filter(s => s.semester === sem);
    }

    // Ordenar de mayor a menor interés (score), o por código si empatan
    filteredScores.sort((a, b) => b.count - a.count || a.code.localeCompare(b.code));

    if (filteredScores.length === 0) {
        scoreItemsContainer.innerHTML = '<div class="empty-state">No hay materias para mostrar.</div>';
        return;
    }

    filteredScores.forEach(item => {
        // Calcular porcentaje con un máximo de visualización adaptativo
        const percentage = Math.min((item.count / MIN_STUDENTS_TO_OPEN) * 100, 100);
        const reached = item.count >= MIN_STUDENTS_TO_OPEN;
        
        const scoreHtml = `
            <div class="score-item ${reached ? 'target-reached' : ''}" id="score-${item.code}">
                <div class="score-item-header">
                    <div class="score-item-info">
                        <span class="score-item-title">${item.name}</span>
                        <div class="score-item-meta">
                            <span>Semestre ${item.semester}°</span>
                            <span>• Código: ${item.code}</span>
                        </div>
                    </div>
                    <span class="score-count-badge">
                        <i class="fa-solid fa-users"></i> ${item.count}
                    </span>
                </div>
                <div class="score-progress-wrapper">
                    <div class="progress-bar-outer">
                        <div class="progress-bar-inner" style="width: ${percentage}%"></div>
                    </div>
                    ${item.count > 0 ? `
                        <button class="btn-details" onclick="openSubjectDetails('${item.code}')">
                            Detalles <i class="fa-solid fa-chevron-right"></i>
                        </button>
                    ` : ''}
                </div>
            </div>
        `;
        scoreItemsContainer.insertAdjacentHTML('beforeend', scoreHtml);
    });
}

// Renderizar tabla de estudiantes inscritos
function renderStudentsTable() {
    studentsTableBody.innerHTML = '';
    const searchTerm = searchStudentInput.value.toLowerCase().trim();

    const filteredStudents = registrations.filter(student => 
        student.name.toLowerCase().includes(searchTerm) || 
        student.code.toLowerCase().includes(searchTerm)
    );

    if (filteredStudents.length === 0) {
        studentsTableBody.innerHTML = `
            <tr>
                <td colspan="4" class="empty-state">
                    <i class="fa-regular fa-folder-open"></i>
                    <p>${searchTerm ? 'No se encontraron coincidencias para la búsqueda.' : 'No hay estudiantes registrados aún.'}</p>
                </td>
            </tr>
        `;
        return;
    }

    // Ordenar por nombre del estudiante alfabéticamente
    filteredStudents.sort((a, b) => a.name.localeCompare(b.name));

    filteredStudents.forEach(student => {
        // Crear mini-tags de las materias
        const subjectTagsHtml = student.subjects.map(code => {
            const subj = SUBJECTS.find(s => s.code === code);
            let shortName = 'Materia';
            if (subj) {
                if (subj.code === 'ELE0300116') {
                    shortName = 'Marketing';
                } else if (subj.name.includes('-')) {
                    shortName = subj.name.split('-')[1].trim().split(' ')[0];
                } else {
                    shortName = subj.name.split(' ')[0];
                }
            }
            return `<span class="subject-mini-tag" title="${subj ? subj.name : code}">${code} (${shortName})</span>`;
        }).join(' ');

        const rowHtml = `
            <tr>
                <td class="td-student-name">${student.name}</td>
                <td>
                    <div class="td-sub-info">
                        <span><strong class="td-lbl-code">Cód:</strong> ${student.code}</span>
                        <span><strong class="td-lbl-phone">Tel:</strong> ${student.phone}</span>
                    </div>
                </td>
                <td>
                    <div class="subject-tag-list">
                        ${subjectTagsHtml}
                    </div>
                </td>
                <td>
                    <div style="display: flex; align-items: center; gap: 0.35rem; justify-content: flex-end;">
                        ${student.signature ? `
                            <button type="button" class="badge-signature-done" onclick="openSignatureModal('${student.code}')" title="Firma registrada. Clic para ver o cambiar">
                                <img src="${student.signature}" class="signature-preview-thumbnail" alt="Firma">
                                <i class="fa-solid fa-check"></i>
                            </button>
                        ` : `
                            <button type="button" class="btn-sign-inline" onclick="openSignatureModal('${student.code}')" title="Firmar carta de solicitud">
                                <i class="fa-solid fa-pen-nib"></i> Firmar
                            </button>
                        `}
                        <button class="btn-icon text-danger" onclick="deleteRegistration('${student.id}')" title="Eliminar registro" aria-label="Eliminar registro">
                            <i class="fa-regular fa-trash-can" style="color: var(--danger-color)"></i>
                        </button>
                    </div>
                </td>
            </tr>
        `;
        studentsTableBody.insertAdjacentHTML('beforeend', rowHtml);
    });
}

// Eliminar registro de estudiante
window.deleteRegistration = async function(id) {
    if (confirm('¿Estás seguro de que deseas eliminar este registro de estudiante?')) {
        registrations = registrations.filter(r => r.id !== id);
        updateUI();
        showToast('Registro eliminado correctamente.', 'success');
        await saveData(null, true, id);
    }
};

// Abrir modal con detalles de estudiantes interesados en una asignatura
window.openSubjectDetails = function(code) {
    const subject = SUBJECTS.find(s => s.code === code);
    if (!subject) return;

    const interested = registrations.filter(r => r.subjects.includes(code));
    
    modalSubjectTitle.textContent = subject.name;
    modalSubjectCode.textContent = `Código: ${subject.code}`;
    modalSubjectCount.textContent = `${interested.length} Estudiantes Interesados`;

    modalStudentsList.innerHTML = '';
    
    if (interested.length === 0) {
        modalStudentsList.innerHTML = '<li>No hay inscritos en esta materia.</li>';
    } else {
        interested.forEach(student => {
            const li = document.createElement('li');
            li.className = 'modal-student-item';
            li.innerHTML = `
                <div class="modal-student-info">
                    <span class="modal-student-name">${student.name}</span>
                    <span class="modal-student-details">Cód: ${student.code}</span>
                </div>
                <a href="https://wa.me/57${student.phone.replace(/\D/g,'')}" target="_blank" class="btn btn-secondary btn-sm" style="color: #25D366; background: rgba(37, 211, 102, 0.1); border-color: rgba(37, 211, 102, 0.2)">
                    <i class="fa-brands fa-whatsapp"></i> Chat
                </a>
            `;
            modalStudentsList.appendChild(li);
        });
    }

    modal.classList.add('active');
};

// Cerrar modal
function closeModal() {
    modal.classList.remove('active');
}

// Mostrar notificaciones Toast
function showToast(message, type = 'success') {
    // Eliminar toasts anteriores si existen
    const activeToasts = document.querySelectorAll('.toast');
    activeToasts.forEach(t => t.remove());

    const toast = document.createElement('div');
    toast.className = `toast ${type}`;
    
    const icon = type === 'success' 
        ? '<i class="fa-solid fa-circle-check" style="color: var(--success-color)"></i>' 
        : '<i class="fa-solid fa-circle-exclamation" style="color: var(--danger-color)"></i>';
        
    toast.innerHTML = `
        ${icon}
        <span>${message}</span>
    `;
    document.body.appendChild(toast);

    // Auto-eliminar después de 3.5 segundos
    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateY(20px)';
        setTimeout(() => toast.remove(), 300);
    }, 3500);
}

// Exportar datos a CSV
function exportToCSV() {
    if (registrations.length === 0) {
        showToast('No hay datos registrados para exportar.', 'error');
        return;
    }

    // Definición de cabeceras
    let csvContent = 'data:text/csv;charset=utf-8,\uFEFF'; // BOM para soportar caracteres especiales en Excel
    csvContent += 'Nombre Completo,Código,Teléfono,Fecha Registro,Firma Registrada,Materias Interesadas\n';

    registrations.forEach(student => {
        const subjectsString = student.subjects.map(code => {
            const subj = SUBJECTS.find(s => s.code === code);
            return subj ? `${code} - ${subj.name}` : code;
        }).join(' | ');

        // Escapar comillas en campos de texto
        const nameEscaped = `"${student.name.replace(/"/g, '""')}"`;
        const codeEscaped = `"${student.code.replace(/"/g, '""')}"`;
        const phoneEscaped = `"${student.phone.replace(/"/g, '""')}"`;
        const dateEscaped = `"${student.date.replace(/"/g, '""')}"`;
        const hasSig = student.signature ? 'SÍ' : 'NO';
        const subjectsEscaped = `"${subjectsString.replace(/"/g, '""')}"`;

        csvContent += `${nameEscaped},${codeEscaped},${phoneEscaped},${dateEscaped},"${hasSig}",${subjectsEscaped}\n`;
    });

    // Descargar el archivo
    const encodedUri = encodeURI(csvContent);
    const link = document.createElement('a');
    link.setAttribute('href', encodedUri);
    
    const dateFormatted = new Date().toISOString().split('T')[0];
    link.setAttribute('download', `Cursos_Vacacionales_Eléctrica_FET_${dateFormatted}.csv`);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    
    showToast('Reporte CSV descargado con éxito.', 'success');
}

// ==========================================================================
// Módulo de Firma Digital (Touch & Mouse - Celular y Computador)
// ==========================================================================

function initSignaturePads() {
    formSigPad = createSignaturePad('sig-canvas-form', 'sig-placeholder-form', 'btn-clear-sig-form');
    modalSigPad = createSignaturePad('sig-canvas-modal', 'sig-placeholder-modal', 'btn-clear-sig-modal');
}

function createSignaturePad(canvasId, placeholderId, clearBtnId) {
    const canvas = document.getElementById(canvasId);
    if (!canvas) return null;
    const ctx = canvas.getContext('2d');
    const placeholder = document.getElementById(placeholderId);
    const clearBtn = document.getElementById(clearBtnId);
    
    let isDrawing = false;
    let hasDrawn = false;
    let lastX = 0;
    let lastY = 0;

    function resize() {
        const rect = canvas.getBoundingClientRect();
        if (rect.width === 0 || rect.height === 0) return;
        const dpr = window.devicePixelRatio || 1;
        
        let tempImg = null;
        if (hasDrawn) {
            tempImg = canvas.toDataURL();
        }

        canvas.width = rect.width * dpr;
        canvas.height = rect.height * dpr;
        ctx.scale(dpr, dpr);
        ctx.strokeStyle = '#042a49'; // Tinta azul marino oscuro tipo bolígrafo
        ctx.lineWidth = 2.4;
        ctx.lineCap = 'round';
        ctx.lineJoin = 'round';

        if (tempImg) {
            loadFromDataURL(tempImg);
        }
    }

    function getCoords(e) {
        const rect = canvas.getBoundingClientRect();
        let clientX = e.clientX;
        let clientY = e.clientY;
        if (e.touches && e.touches.length > 0) {
            clientX = e.touches[0].clientX;
            clientY = e.touches[0].clientY;
        }
        return {
            x: clientX - rect.left,
            y: clientY - rect.top
        };
    }

    function startDrawing(e) {
        isDrawing = true;
        const coords = getCoords(e);
        lastX = coords.x;
        lastY = coords.y;
        if (placeholder) placeholder.classList.add('hidden');
    }

    function draw(e) {
        if (!isDrawing) return;
        if (e.cancelable && e.type.startsWith('touch')) {
            e.preventDefault(); // Evita scroll de página al dibujar en celulares
        }
        const coords = getCoords(e);
        ctx.beginPath();
        ctx.moveTo(lastX, lastY);
        ctx.lineTo(coords.x, coords.y);
        ctx.stroke();
        lastX = coords.x;
        lastY = coords.y;
        hasDrawn = true;
    }

    function stopDrawing() {
        if (isDrawing) {
            isDrawing = false;
        }
    }

    // Eventos Mouse
    canvas.addEventListener('mousedown', startDrawing);
    canvas.addEventListener('mousemove', draw);
    window.addEventListener('mouseup', stopDrawing);

    // Eventos Touch (Móviles / Tablets)
    canvas.addEventListener('touchstart', (e) => {
        if (e.cancelable) e.preventDefault();
        startDrawing(e);
    }, { passive: false });
    canvas.addEventListener('touchmove', draw, { passive: false });
    canvas.addEventListener('touchend', stopDrawing);
    canvas.addEventListener('touchcancel', stopDrawing);

    if (clearBtn) {
        clearBtn.addEventListener('click', () => {
            clear();
        });
    }

    function clear() {
        const rect = canvas.getBoundingClientRect();
        ctx.clearRect(0, 0, rect.width, rect.height);
        hasDrawn = false;
        if (placeholder) placeholder.classList.remove('hidden');
    }

    function toDataURL() {
        if (!hasDrawn) return '';
        // Normalizar a dimensiones estándar óptimas (450x180) para celular y PC
        // Garantiza peso ligero (<15KB), envío instantáneo en 3G/4G y compatibilidad keepalive
        const targetW = 450;
        const targetH = 180;
        const normCanvas = document.createElement('canvas');
        normCanvas.width = targetW;
        normCanvas.height = targetH;
        const normCtx = normCanvas.getContext('2d');
        normCtx.drawImage(canvas, 0, 0, targetW, targetH);
        return normCanvas.toDataURL('image/png');
    }

    function loadFromDataURL(dataUrl) {
        if (!dataUrl) {
            clear();
            return;
        }
        const img = new Image();
        img.onload = () => {
            const rect = canvas.getBoundingClientRect();
            ctx.clearRect(0, 0, rect.width, rect.height);
            ctx.drawImage(img, 0, 0, rect.width, rect.height);
            hasDrawn = true;
            if (placeholder) placeholder.classList.add('hidden');
        };
        img.src = dataUrl;
    }

    setTimeout(resize, 150);
    window.addEventListener('resize', resize);

    return {
        resize,
        clear,
        hasDrawn: () => hasDrawn,
        toDataURL,
        loadFromDataURL
    };
}

// Abrir Modal de Firma Rápida
window.openSignatureModal = function(studentCode = null) {
    if (!modalSignature) return;

    // Rellenar lista de estudiantes
    modalSigStudentSelect.innerHTML = '<option value="">-- Selecciona tu nombre de la lista --</option>';
    const sorted = [...registrations].sort((a, b) => a.name.localeCompare(b.name));
    
    sorted.forEach(st => {
        const opt = document.createElement('option');
        opt.value = st.code;
        const sigMark = st.signature ? ' (✓ Con Firma)' : ' (✍️ Pendiente)';
        opt.textContent = `${st.name} - Cód: ${st.code}${sigMark}`;
        modalSigStudentSelect.appendChild(opt);
    });

    const activeCode = studentCode || localStorage.getItem('fet_vacacionales_active_student_code') || '';
    if (activeCode) {
        modalSigStudentSelect.value = activeCode;
    }

    onModalStudentSelectChange();

    modalSignature.classList.add('active');
    if (modalSigPad) {
        setTimeout(() => modalSigPad.resize(), 120);
    }
};

function onModalStudentSelectChange() {
    const selectedCode = modalSigStudentSelect.value;
    const student = registrations.find(r => r.code === selectedCode);

    if (modalSigPad) {
        modalSigPad.clear();
    }

    if (student) {
        const subjNames = student.subjects.map(c => {
            const s = SUBJECTS.find(sub => sub.code === c);
            return s ? `${s.name} (${c})` : c;
        }).join(' • ');

        modalSigSubjectsList.innerHTML = `<span style="color: var(--accent-primary);"><i class="fa-solid fa-file-contract"></i> ${subjNames || 'Sin materias asignadas'}</span>`;

        if (student.signature && modalSigPad) {
            modalSigPad.loadFromDataURL(student.signature);
        }
    } else {
        modalSigSubjectsList.textContent = 'Selecciona tu nombre arriba para ver tus asignaturas y firmar.';
    }
}

async function saveModalSignature() {
    const selectedCode = modalSigStudentSelect.value;
    if (!selectedCode) {
        showToast('Debes seleccionar tu nombre o código estudiantil.', 'error');
        return;
    }

    const student = registrations.find(r => r.code === selectedCode);
    if (!student) {
        showToast('Estudiante no encontrado en la lista.', 'error');
        return;
    }

    if (!modalSigPad || !modalSigPad.hasDrawn()) {
        showToast('Por favor dibuja tu firma en el recuadro antes de guardar.', 'error');
        return;
    }

    const sigData = modalSigPad.toDataURL();
    student.signature = sigData;

    // 1. Guardar de inmediato en localStorage y actualizar UI (reserva local infalible)
    localStorage.setItem('fet_vacacionales_active_student_code', student.code);
    saveToLocalStorage();
    updateUI();

    // 2. Bloquear UI del modal con spinner para impedir cierres prematuros en celulares
    const origHtml = btnSaveSigModal.innerHTML;
    btnSaveSigModal.disabled = true;
    if (btnCancelSigModal) btnCancelSigModal.disabled = true;
    if (btnCloseSigModal) btnCloseSigModal.disabled = true;
    if (modalSigStudentSelect) modalSigStudentSelect.disabled = true;
    btnSaveSigModal.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Guardando y subiendo a la nube...';
    btnSaveSigModal.style.opacity = '0.9';

    try {
        // 3. Sincronizar en la nube con reintento automático y keepalive
        await syncStudentToCloud(student, false);

        // 4. Confirmación visual verde antes de cerrar
        btnSaveSigModal.innerHTML = '<i class="fa-solid fa-circle-check"></i> ¡Sincronizado con éxito en la nube!';
        btnSaveSigModal.style.background = '#10b981';
        btnSaveSigModal.style.borderColor = '#10b981';
        showToast(`¡Firma respaldada y sincronizada exitosamente para ${student.name}!`, 'success');

        // Pausa de 850ms para que el estudiante certifique el visto bueno
        setTimeout(() => {
            closeSignatureModal();
            // Restaurar estado del botón
            btnSaveSigModal.disabled = false;
            if (btnCancelSigModal) btnCancelSigModal.disabled = false;
            if (btnCloseSigModal) btnCloseSigModal.disabled = false;
            if (modalSigStudentSelect) modalSigStudentSelect.disabled = false;
            btnSaveSigModal.innerHTML = origHtml;
            btnSaveSigModal.style.background = '';
            btnSaveSigModal.style.borderColor = '';
            btnSaveSigModal.style.opacity = '';
        }, 850);

        // Notificar en background
        fetch(BACKEND_URL).then(r => r.json()).then(cloudData => {
            checkAndSyncPendingSignatures(cloudData);
        }).catch(() => {});

    } catch (err) {
        console.error("Fallo al subir firma a la nube:", err);
        // Desbloquear controles para permitir reintento manual
        btnSaveSigModal.disabled = false;
        if (btnCancelSigModal) btnCancelSigModal.disabled = false;
        if (btnCloseSigModal) btnCloseSigModal.disabled = false;
        if (modalSigStudentSelect) modalSigStudentSelect.disabled = false;
        btnSaveSigModal.style.opacity = '';
        btnSaveSigModal.style.background = '#dc2626';
        btnSaveSigModal.style.borderColor = '#dc2626';
        btnSaveSigModal.innerHTML = '<i class="fa-solid fa-rotate-right"></i> Reintentar Sincronización';

        showToast('Tu firma está guardada en este celular, pero no se pudo subir a la nube por mala conexión. Presiona "Reintentar Sincronización".', 'error');
    }
}

function closeSignatureModal() {
    if (modalSignature) {
        modalSignature.classList.remove('active');
    }
}
