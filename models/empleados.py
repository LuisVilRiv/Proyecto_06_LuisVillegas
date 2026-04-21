from peewee import CharField, FloatField, BooleanField, ForeignKeyField
from models.db import BaseModel
from models.secciones import SeccionModel

class EmpleadoModel(BaseModel):
    nombre = CharField()
    tipo = CharField()
    especialidad = CharField(null=True)
    salario_mes = FloatField()
    seccion = ForeignKeyField(SeccionModel, backref='personal', null=True)
    turno = CharField(default='mañana')
    activo = BooleanField(default=True)

    class Meta:
        table_name = 'empleados'

    def to_domain(self):
        import domain.personal as dom
        mapeo = {
            'tecnico': dom.Tecnico,
            'divulgador': dom.Divulgador,
            'cocinero': dom.Cocinero,
            'especializado': dom.TecnicoEspecializado
        }
        cls_dom = mapeo.get(self.tipo, dom.EmpleadoBase)
        return cls_dom(
            id=self.id,
            nombre=self.nombre,
            activo=self.activo,
            salario=self.salario_mes,
            turno=self.turno,
            seccion_asignada=self.seccion_id
        )

    @classmethod
    def from_domain(cls, obj):
        data = {
            'nombre': obj.nombre,
            'salario_mes': obj.salario,
            'turno': obj.turno,
            'seccion': obj.seccion_asignada,
            'activo': obj.activo
        }
        registro, created = cls.get_or_create(id=obj.id, defaults=data)
        if not created:
            for key, value in data.items():
                setattr(registro, key, value)
            registro.save()
        return registro