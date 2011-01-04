#include <Python.h>

/* static variables */

static PyObject *exiftranError;

/* Function declarations */

static PyObject *libexiftran_run(PyObject *dummy, PyObject *args);

/* ------------------------------------------------------- */
static PyObject *
libexiftran_run(PyObject *self, PyObject *args)
{
    const char *filename;
    int action,rc;


    if (!PyArg_ParseTuple(args, "is", &action, &filename))
        return NULL;
//    printf("Got action=%i for filename %s\n",action,filename);
    Py_BEGIN_ALLOW_THREADS;
    rc = pylib(action, filename);
    Py_END_ALLOW_THREADS;

    if (rc!=0) printf("Error during libexiftran.run(%i,%s)",action,filename);
//    printf("Recived code %i",rc);
    return Py_BuildValue("i", rc);
}


/* Module methods */
static PyMethodDef libexiftranMethods[] ={
    {"run", libexiftran_run, METH_VARARGS},
    {NULL,NULL, 0, NULL} /* sentinel */
};


/* Initialise the module */
PyMODINIT_FUNC
initlibexiftran(void)
{
    PyObject *m, *d;
    /* Create the module and add the functions */
    m = Py_InitModule("libexiftran", libexiftranMethods);

    /* Add some symbolic constants to the module */
//    d = PyModule_GetDict(m);

//    import_array();
//    libexiftranError = PyErr_NewException("libexiftran.error", NULL, NULL);
//    PyDict_SetItemString(d, "error", libexiftranError);
}

