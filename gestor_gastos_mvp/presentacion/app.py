"""Interfaz Tkinter local: movimientos, categorías, filtros, resumen y gráfico."""
import tkinter as tk
from datetime import date
from tkinter import ttk, messagebox
from pathlib import Path
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from datos.conexion import abrir_db, ruta_default
from datos.repositorio import Repositorio
from negocio.movimiento import ValidacionError


class App(tk.Tk):
    """Interfaz única con gestión de errores no reveladores."""
    def __init__(self, db_path: str | Path | None = None):
        super().__init__()
        self.title('Gestor de Gastos Personales | MVP Alpha')
        self.geometry('1050x730')
        self.minsize(880,650)
        self.configure(bg='#f3f6fa')
        self.con = abrir_db(db_path if db_path is not None else ruta_default())
        self.repo = Repositorio(self.con)
        self._cat_ids = {}
        self._sel_mov = None
        self._sel_cat = None
        self._style()
        self._tabs()
        self._refrescar_todo()
        self.protocol('WM_DELETE_WINDOW',self._cerrar)

    def _style(self):
        style=ttk.Style(self)
        style.theme_use('clam')
        style.configure('TNotebook.Tab',padding=(16,10),font=('Segoe UI',10,'bold'))
        style.configure('Treeview',rowheight=27,font=('Segoe UI',9))
        style.configure('Treeview.Heading',font=('Segoe UI',9,'bold'))
        style.configure('TButton',padding=7)

    def _tabs(self):
        root=ttk.Frame(self,padding=16)
        root.pack(fill='both',expand=True)
        ttk.Label(root,text='GESTOR DE GASTOS PERSONALES',font=('Segoe UI',19,'bold')).pack(anchor='w')
        ttk.Label(root,text='Prototipo local · Datos en pesos chilenos (CLP) · Sin conexión a internet').pack(anchor='w',pady=(2,10))
        tabs=ttk.Notebook(root)
        tabs.pack(fill='both',expand=True)
        self.tab_mov=ttk.Frame(tabs,padding=10)
        self.tab_cat=ttk.Frame(tabs,padding=10)
        self.tab_res=ttk.Frame(tabs,padding=10)
        tabs.add(self.tab_mov,text='Movimientos')
        tabs.add(self.tab_cat,text='Categorías')
        tabs.add(self.tab_res,text='Resumen y gráfico')
        self._tab_movimientos()
        self._tab_categorias()
        self._tab_resumen()

    def _tab_movimientos(self):
        form=ttk.LabelFrame(self.tab_mov,text='Registrar / editar movimiento',padding=10)
        form.pack(fill='x')
        self.tipo=tk.StringVar(value='gasto')
        self.monto=tk.StringVar()
        self.fecha=tk.StringVar(value=date.today().isoformat())
        self.categoria=tk.StringVar()
        self.descripcion=tk.StringVar()
        for col,(txt,var) in enumerate([('Tipo',self.tipo),('Monto CLP',self.monto),('Fecha (AAAA-MM-DD)',self.fecha),('Categoría',self.categoria)]):
            ttk.Label(form,text=txt).grid(row=0,column=col,sticky='w',padx=4)
            if col==0:
                w=ttk.Combobox(form,textvariable=var,values=['ingreso','gasto'],state='readonly',width=15)
                w.bind('<<ComboboxSelected>>',lambda e:self._cargar_categorias_combo())
            elif col==3:
                self.cmb_categoria=ttk.Combobox(form,textvariable=var,state='readonly',width=24)
                w=self.cmb_categoria
            else: w=ttk.Entry(form,textvariable=var,width=23)
            w.grid(row=1,column=col,sticky='ew',padx=4,pady=(3,8))
        ttk.Label(form,text='Descripción (hasta 120 caracteres)').grid(row=2,column=0,columnspan=3,sticky='w')
        ttk.Entry(form,textvariable=self.descripcion).grid(row=3,column=0,columnspan=3,sticky='ew',padx=3)
        for c in range(4):form.columnconfigure(c,weight=1)
        ttk.Button(form,text='Guardar movimiento',command=self._guardar_movimiento).grid(row=3,column=3,sticky='ew',padx=4)
        tools=ttk.Frame(self.tab_mov)
        tools.pack(fill='x',pady=10)
        self.filtro_mes=tk.StringVar(value=date.today().strftime('%Y-%m'))
        ttk.Label(tools,text='Mes:').pack(side='left')
        ttk.Entry(tools,textvariable=self.filtro_mes,width=9).pack(side='left',padx=5)
        ttk.Label(tools,text='Categoría:').pack(side='left',padx=(12,2))
        self.filtro_cat=tk.StringVar(value='Todas')
        self.cmb_filtro_cat=ttk.Combobox(tools,textvariable=self.filtro_cat,state='readonly',width=20)
        self.cmb_filtro_cat.pack(side='left',padx=3)
        ttk.Button(tools,text='Filtrar / actualizar',command=self._cargar_movimientos).pack(side='left',padx=3)
        ttk.Button(tools,text='Todos',command=self._todos_movimientos).pack(side='left',padx=3)
        ttk.Button(tools,text='Editar seleccionado',command=self._editar_seleccion).pack(side='left',padx=3)
        ttk.Button(tools,text='Eliminar seleccionado',command=self._eliminar_seleccion).pack(side='left',padx=3)
        cols=('id','fecha','tipo','categoria','monto','descripcion')
        self.tabla=ttk.Treeview(self.tab_mov,columns=cols,show='headings',selectmode='browse')
        for nombre,ancho in [('id',55),('fecha',105),('tipo',100),('categoria',140),('monto',120),('descripcion',340)]:
            self.tabla.heading(nombre,text=nombre.capitalize())
            self.tabla.column(nombre,width=ancho,stretch=nombre=='descripcion')
        self.tabla.pack(fill='both',expand=True)

    def _tab_categorias(self):
        row=ttk.LabelFrame(self.tab_cat,text='Crear / editar categoría',padding=12)
        row.pack(fill='x')
        self.cat_nombre=tk.StringVar()
        self.cat_tipo=tk.StringVar(value='gasto')
        ttk.Label(row,text='Nombre').grid(row=0,column=0,sticky='w')
        ttk.Entry(row,textvariable=self.cat_nombre,width=35).grid(row=1,column=0,padx=5)
        ttk.Label(row,text='Tipo').grid(row=0,column=1,sticky='w')
        ttk.Combobox(row,textvariable=self.cat_tipo,values=['ingreso','gasto'],state='readonly',width=18).grid(row=1,column=1,padx=5)
        ttk.Button(row,text='Guardar categoría',command=self._guardar_categoria).grid(row=1,column=2,padx=5)
        ttk.Button(row,text='Eliminar seleccionada',command=self._eliminar_categoria).grid(row=1,column=3,padx=5)
        ttk.Button(row,text='Limpiar selección',command=self._limpiar_cat).grid(row=1,column=4,padx=5)
        cols=('id','nombre','tipo')
        self.tabla_cat=ttk.Treeview(self.tab_cat,columns=cols,show='headings')
        for x in cols:self.tabla_cat.heading(x,text=x.capitalize())
        self.tabla_cat.pack(fill='both',expand=True,pady=12)
        self.tabla_cat.bind('<<TreeviewSelect>>',self._seleccionar_categoria)

    def _tab_resumen(self):
        top=ttk.Frame(self.tab_res)
        top.pack(fill='x')
        self.mes_res=tk.StringVar(value=date.today().strftime('%Y-%m'))
        ttk.Label(top,text='Mes AAAA-MM:').pack(side='left')
        ttk.Entry(top,textvariable=self.mes_res,width=12).pack(side='left',padx=8)
        ttk.Button(top,text='Calcular resumen',command=self._actualizar_resumen).pack(side='left')
        self.lbl_ing=ttk.Label(self.tab_res,text='Ingresos: $0',font=('Segoe UI',13,'bold'))
        self.lbl_gas=ttk.Label(self.tab_res,text='Gastos: $0',font=('Segoe UI',13,'bold'))
        self.lbl_saldo=ttk.Label(self.tab_res,text='Saldo: $0',font=('Segoe UI',13,'bold'))
        for label in (self.lbl_ing,self.lbl_gas,self.lbl_saldo):label.pack(anchor='w',pady=5)
        self.fig=Figure(figsize=(9,4.8),dpi=90)
        self.ax=self.fig.add_subplot(111)
        self.fig.tight_layout(pad=3)
        self.canvas=FigureCanvasTkAgg(self.fig,master=self.tab_res)
        self.canvas.get_tk_widget().pack(fill='both',expand=True)

    def _avisar_error(self,error: Exception):
        if isinstance(error,ValidacionError):mensaje=str(error)
        elif isinstance(error,Exception):mensaje='No se pudo completar la operación. Verifique los datos y permisos.'
        messagebox.showerror('Operación no realizada',mensaje)

    def _refrescar_todo(self):
        self._cargar_categorias()
        self._cargar_categorias_combo()
        self._cargar_filtro_categoria()
        self._cargar_movimientos()
        self._actualizar_resumen()

    def _cargar_categorias_combo(self):
        cats=self.repo.categorias(self.tipo.get())
        self._cat_ids={f"{c['id']} · {c['nombre']}":c['id'] for c in cats}
        self.cmb_categoria['values']=list(self._cat_ids)
        if self.categoria.get() not in self._cat_ids:self.categoria.set('')

    def _cargar_filtro_categoria(self):
        self._filtro_cat_ids = {'Todas': None}
        for c in self.repo.categorias():
            nombre = f"{c['id']} · {c['nombre']} ({c['tipo']})"
            self._filtro_cat_ids[nombre] = c['id']
        self.cmb_filtro_cat['values'] = list(self._filtro_cat_ids)
        if self.filtro_cat.get() not in self._filtro_cat_ids:
            self.filtro_cat.set('Todas')

    def _guardar_movimiento(self):
        try:
            cat=self._cat_ids.get(self.categoria.get())
            if self._sel_mov is None:
                self.repo.registrar(self.tipo.get(),self.monto.get(),self.fecha.get(),cat,self.descripcion.get())
            else:
                self.repo.editar_movimiento(self._sel_mov,self.tipo.get(),self.monto.get(),self.fecha.get(),cat,self.descripcion.get())
            self._sel_mov=None
            self.monto.set('')
            self.descripcion.set('')
            self._refrescar_todo()
        except Exception as error:self._avisar_error(error)

    def _cargar_movimientos(self):
        try: rows=self.repo.movimientos(self.filtro_mes.get().strip() or None,
                                       self._filtro_cat_ids.get(self.filtro_cat.get()))
        except Exception as error:
            self._avisar_error(error);return
        self._mov_data={item['id']:item for item in rows}
        for x in self.tabla.get_children():self.tabla.delete(x)
        for item in rows:
            self.tabla.insert('', 'end', iid=str(item['id']),values=(item['id'],item['fecha'],item['tipo'],
                                 item['categoria'],f"$ {item['monto']:,}".replace(',','.'),item['descripcion']))

    def _todos_movimientos(self):
        self.filtro_mes.set('');self.filtro_cat.set('Todas');self._cargar_movimientos()

    def _editar_seleccion(self):
        sel=self.tabla.selection()
        if not sel:return
        item=self._mov_data[int(sel[0])]
        self._sel_mov=item['id']
        self.tipo.set(item['tipo'])
        self._cargar_categorias_combo()
        for nombre,ident in self._cat_ids.items():
            if ident==item['categoria_id']:self.categoria.set(nombre)
        self.monto.set(str(item['monto']))
        self.fecha.set(item['fecha'])
        self.descripcion.set(item['descripcion'])

    def _eliminar_seleccion(self):
        sel=self.tabla.selection()
        if not sel:return
        if messagebox.askyesno('Confirmar borrado','¿Eliminar el movimiento seleccionado?'):
            try:self.repo.eliminar_movimiento(int(sel[0]));self._refrescar_todo()
            except Exception as error:self._avisar_error(error)

    def _cargar_categorias(self):
        for x in self.tabla_cat.get_children():self.tabla_cat.delete(x)
        for c in self.repo.categorias():
            self.tabla_cat.insert('','end',iid=str(c['id']),values=(c['id'],c['nombre'],c['tipo']))

    def _seleccionar_categoria(self,event=None):
        sel=self.tabla_cat.selection()
        if not sel:return
        self._sel_cat=int(sel[0])
        _,nombre,tipo=self.tabla_cat.item(sel[0])['values']
        self.cat_nombre.set(nombre);self.cat_tipo.set(tipo)

    def _limpiar_cat(self):
        self._sel_cat=None;self.cat_nombre.set('');self.cat_tipo.set('gasto')

    def _guardar_categoria(self):
        try:
            if self._sel_cat is None:self.repo.crear_categoria(self.cat_nombre.get(),self.cat_tipo.get())
            else:self.repo.editar_categoria(self._sel_cat,self.cat_nombre.get(),self.cat_tipo.get())
            self._limpiar_cat();self._refrescar_todo()
        except Exception as error:self._avisar_error(error)

    def _eliminar_categoria(self):
        if self._sel_cat is None:return
        if messagebox.askyesno('Confirmar borrado','¿Eliminar la categoría seleccionada?'):
            try:self.repo.eliminar_categoria(self._sel_cat);self._limpiar_cat();self._refrescar_todo()
            except Exception as error:self._avisar_error(error)

    def _actualizar_resumen(self):
        try:
            mes=self.mes_res.get()
            datos=self.repo.resumen_mensual(mes)
            graficos=self.repo.gastos_por_categoria(mes)
            self.lbl_ing.config(text=f"Ingresos: $ {datos['ingresos']:,}".replace(',','.'))
            self.lbl_gas.config(text=f"Gastos: $ {datos['gastos']:,}".replace(',','.'))
            self.lbl_saldo.config(text=f"Saldo: $ {datos['saldo']:,}".replace(',','.'))
            self.ax.clear()
            if graficos:
                self.ax.barh([d['categoria'] for d in graficos][::-1],
                             [d['total'] for d in graficos][::-1],color='#3182bd')
                self.ax.set_xlabel('Total de gastos (CLP)')
            else:self.ax.text(.5,.5,'Sin gastos registrados para el mes',ha='center',va='center',transform=self.ax.transAxes)
            self.ax.set_title(f'Gastos por categoría · {mes}')
            self.fig.tight_layout(pad=2)
            self.canvas.draw_idle()
        except Exception as error:self._avisar_error(error)

    def _cerrar(self):
        self.con.close();self.destroy()


if __name__ == '__main__':
    App().mainloop()
