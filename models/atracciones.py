from peewee import CharField, IntegerField, FloatField, BooleanField, ForeignKeyField
from models.db import BaseModel
from models.secciones import SeccionModel

class AtraccionModel(BaseModel):
    nombre = CharField()
    tipo = CharField()
    seccion = ForeignKeyField(SeccionModel, backref='atracciones')
    capacidad_max = IntegerField(default=20)
    duracion_min = IntegerField(default=10)
    altura_minima_cm = IntegerField(default=0)
    integridad = FloatField(default=100.0)
    en_mantenimiento = BooleanField(default=False)
    activo = BooleanField(default=True)
    precio_base = FloatField(default=0.0)

    class Meta:
        table_name = 'atracciones'

    def to_domain(self):
        import domain.atracciones as dom
        mapeo = {
            'mecanica': dom.AtraccionMecanica,
            'simulador': dom.AtraccionSimulador,
            'interactiva': dom.AtraccionInteractiva,
            'laboratorio': dom.AtraccionLaboratorio,
            'extreme': dom.AtraccionExtreme
        }
        cls_dom = mapeo.get(self.tipo, dom.AtraccionMecanica)
        return cls_dom(
            id=self.id,
            nombre=self.nombre,
            activo=self.activo,
            integridad=self.integridad,
            en_mantenimiento=self.en_mantenimiento,
            capacidad_max=self.capacidad_max,
            duracion_min=self.duracion_min,
            precio_base=self.precio_base,
            altura_minima_cm=self.altura_minima_cm,
            seccion_id=self.seccion_id
        )

    @classmethod
    def from_domain(cls, obj):
        data = {
            'nombre': obj.nombre,
            'activo': obj.activo,
            'integridad': obj.integridad,
            'en_mantenimiento': obj.en_mantenimiento,
            'capacidad_max': obj.capacidad_max,
            'duracion_min': obj.duracion_min,
            'precio_base': obj.precio_base,
            'altura_minima_cm': obj.altura_minima_cm,
            'seccion': obj.seccion_id
        }
        registro, created = cls.get_or_create(id=obj.id, defaults=data)
        if not created:
            for key, value in data.items():
                setattr(registro, key, value)
            registro.save()
        return registro