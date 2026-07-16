"""Investigational product endpoints."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app import crud, models, schemas
from app.database import get_db

router = APIRouter(prefix="/ip", tags=["ip"])


@router.post("/products", response_model=schemas.InvestigationalProductOut)
async def create_product(data: schemas.InvestigationalProductCreate, db: AsyncSession = Depends(get_db)) -> schemas.InvestigationalProductOut:
    product = await crud.create_investigational_product(db, data)
    return schemas.InvestigationalProductOut.model_validate(product)


@router.get("/products/{product_id}", response_model=schemas.InvestigationalProductOut)
async def get_product(product_id: int, db: AsyncSession = Depends(get_db)) -> schemas.InvestigationalProductOut:
    product = await crud.get_investigational_product(db, product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return schemas.InvestigationalProductOut.model_validate(product)


@router.post("/shipments", response_model=schemas.IpShipmentOut)
async def create_shipment(data: schemas.IpShipmentCreate, db: AsyncSession = Depends(get_db)) -> schemas.IpShipmentOut:
    shipment = await crud.create_ip_shipment(db, data)
    return schemas.IpShipmentOut.model_validate(shipment)


@router.post("/shipments/{shipment_id}/receive", response_model=schemas.IpShipmentOut)
async def receive_shipment(shipment_id: int, received_by: str, condition_ok: bool, db: AsyncSession = Depends(get_db)) -> schemas.IpShipmentOut:
    shipment = await db.get(models.IpShipment, shipment_id)
    if not shipment:
        raise HTTPException(status_code=404, detail="Shipment not found")
    updated = await crud.receive_shipment(db, shipment, received_by, condition_ok)
    return schemas.IpShipmentOut.model_validate(updated)


@router.post("/dispenses", response_model=schemas.IpDispenseOut)
async def create_dispense(data: schemas.IpDispenseCreate, db: AsyncSession = Depends(get_db)) -> schemas.IpDispenseOut:
    dispense = await crud.create_ip_dispense(db, data)
    return schemas.IpDispenseOut.model_validate(dispense)


@router.post("/dispenses/{dispense_id}/destroy", response_model=schemas.IpDispenseOut)
async def destroy_dispense(dispense_id: int, data: schemas.IpDestroy, db: AsyncSession = Depends(get_db)) -> schemas.IpDispenseOut:
    dispense = await db.get(models.IpDispense, dispense_id)
    if not dispense:
        raise HTTPException(status_code=404, detail="Dispense not found")
    updated = await crud.destroy_ip_dispense(db, dispense, data)
    return schemas.IpDispenseOut.model_validate(updated)
