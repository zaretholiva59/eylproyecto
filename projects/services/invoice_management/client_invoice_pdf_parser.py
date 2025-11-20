from decimal import Decimal
import re
import os
import tempfile
from typing import Dict, Any, Optional, List

# ============================================================================
# CONFIGURACIÓN DE RUTAS PARA WINDOWS
# ============================================================================

# Configurar Tesseract
try:
    import pytesseract
    TESSERACT_PATH = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    if os.path.exists(TESSERACT_PATH):
        pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        print("✅ Tesseract configurado")
    else:
        print("⚠️ Tesseract no encontrado en ruta específica")
except ImportError:
    print("⚠️ pytesseract no instalado")

# Configurar Poppler
POPPLER_PATH = r"C:\Users\zareth.oliva\Desktop\poppler-25.07.0\Library\bin"
if POPPLER_PATH:
    pdfinfo_path = os.path.join(POPPLER_PATH, 'pdfinfo.exe')
    if os.path.exists(pdfinfo_path):
        print(f"✅ Poppler encontrado en: {POPPLER_PATH}")
    else:
        print("⚠️ Poppler no encontrado - PDFs escaneados no podrán procesarse")
        print("   Verificar ruta:", POPPLER_PATH)
        POPPLER_PATH = None
else:
    print("⚠️ Poppler no configurado")

class ClientInvoicePDFParser:
    """
    Parser mejorado para extraer datos de facturas PDF con mejor detección de OCR
    """
    def parse_uploaded_pdf(self, pdf_file) -> Dict[str, Any]:
        """
        Procesa un archivo PDF o imagen subido vía Django.
        """
        temp_path = None
        try:
            file_name = getattr(pdf_file, 'name', 'Unknown')
            print(f"\n{'='*60}")
            print(f"🔍 INICIANDO ANÁLISIS: {file_name}")
            print(f"{'='*60}\n")
            
            # Determinar extensión del archivo
            file_ext = os.path.splitext(file_name.lower())[1]
            is_image = file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
            is_pdf = file_ext == '.pdf'

            # Guardar archivo temporal
            if hasattr(pdf_file, 'temporary_file_path'):
                try:
                    temp_path = pdf_file.temporary_file_path()
                    print(f"📁 Usando archivo temporal de Django: {temp_path}")
                except Exception:
                    temp_path = None

            if not temp_path:
                suffix = file_ext if file_ext else ('.png' if is_image else '.pdf')
                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
                temp_path = tmp.name
                print(f"📁 Creando archivo temporal: {temp_path}")
                
                # Escribir contenido del archivo
                pdf_file.seek(0)
                with open(temp_path, 'wb') as destination:
                    for chunk in pdf_file.chunks():
                        destination.write(chunk)

            # Detectar el tipo real del archivo (no solo por extensión)
            file_type = self._detect_file_type(temp_path, file_name)
            print(f"🔍 Tipo de archivo detectado: {file_type}")
            
            if file_type == 'image':
                print("🖼️  Archivo detectado como IMAGEN (por contenido)")
                data = self.parse_image_with_ocr(temp_path)
            elif file_type == 'pdf_image':  # PDF que es realmente una imagen
                print("📄🖼️  PDF detectado como imagen escaneada")
                data = self.parse_pdf_with_ocr(temp_path)
            else:
                print("📄 Archivo detectado como PDF con texto")
                data = self.parse_pdf_smart(temp_path)

            print(f"\n{'='*60}")
            print(f"✅ ANÁLISIS COMPLETADO")
            print(f"{'='*60}")
            print(f"📊 Campos detectados: {len(data)}")
            for key, value in data.items():
                print(f"   ✓ {key}: {value}")
            print(f"{'='*60}\n")

            return data
            
        except Exception as e:
            print(f"\n❌ ERROR CRÍTICO: {e}")
            import traceback
            traceback.print_exc()
            return {}
        finally:
            # Limpiar archivo temporal de manera segura
            if temp_path and os.path.exists(temp_path):
                try:
                    os.remove(temp_path)
                    print(f"🗑️  Archivo temporal eliminado: {temp_path}")
                except Exception as e:
                    print(f"⚠️  No se pudo eliminar temporal: {e}")
    
    def _detect_file_type(self, file_path: str, file_name: str) -> str:
        """
        Detecta el tipo real del archivo (no solo por extensión)
        """
        file_ext = os.path.splitext(file_name.lower())[1]
        
        # Si la extensión es de imagen, es imagen
        if file_ext in ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']:
            return 'image'
        
        # Si es PDF, verificar si realmente contiene texto o es solo imagen
        if file_ext == '.pdf':
            try:
                # Intentar extraer texto del PDF
                text = self._extract_text_improved(file_path)
                if text and len(text.strip()) > 100 and not self._is_text_garbled(text):
                    return 'pdf_text'
                else:
                    return 'pdf_image'  # PDF que es realmente una imagen
            except:
                return 'pdf_image'  # Si hay error, asumir que es imagen
        
        # Por defecto, tratar como PDF
        return 'pdf_text'
    
    def parse_pdf_with_ocr(self, pdf_path: str) -> Dict[str, Any]:
        """
        Procesa un PDF que es realmente una imagen usando OCR
        """
        print("🔬 Procesando PDF como imagen con OCR...")
        text = _extract_text_from_pdf_with_ocr(pdf_path)
        
        if not text:
            print("❌ No se pudo extraer texto del PDF con OCR")
            return {}
        
        print(f"✅ Texto extraído: {len(text)} caracteres")
        # Limpiar texto OCR
        text = self._clean_ocr_text(text)
        print("📝 Texto después de limpieza:")
        print("-" * 50)
        print(text[:800])
        print("-" * 50)
        
        normalized = self._normalize(text)
        return self._parse_text(normalized)
    
    def parse_pdf_smart(self, pdf_path: str) -> Dict[str, Any]:
        """
        Método inteligente que decide si usar extracción de texto o OCR
        """
        print("\n🔬 PASO 1: Intentando extracción de texto...")
        
        # Intentar extraer texto primero
        text = self._extract_text_improved(pdf_path)
        
        # Evaluar calidad del texto extraído
        needs_ocr = False
        
        if not text:
            print("⚠️  No se extrajo texto alguno")
            needs_ocr = True
        elif len(text.strip()) < 100:  # Aumentado a 100 caracteres mínimos
            print(f"⚠️  Texto muy corto ({len(text)} chars) - probablemente imagen")
            needs_ocr = True
        elif self._is_text_garbled(text):
            print("⚠️  Texto parece ser basura o ilegible")
            needs_ocr = True
        elif not self._has_invoice_keywords(text):
            print("⚠️  No se detectaron palabras clave de factura")
            needs_ocr = True
        else:
            print(f"✅ Texto extraído correctamente ({len(text)} chars)")
            # Mostrar solo preview del texto
            preview = text[:300].replace('\n', ' ')
            print(f"📝 Preview: {preview}...")
        
        # Si el texto no es útil, usar OCR
        if needs_ocr:
            print("\n🔬 PASO 2: Aplicando OCR...")
            ocr_text = _extract_text_from_pdf_with_ocr(pdf_path)
            
            if ocr_text and len(ocr_text.strip()) >= 50:
                print(f"✅ OCR exitoso ({len(ocr_text)} chars)")
                # Limpiar texto OCR de artefactos
                ocr_text = self._clean_ocr_text(ocr_text)
                text = ocr_text
                print("📝 Texto OCR después de limpieza:")
                print("-" * 50)
                print(text[:500])
                print("-" * 50)
            else:
                print("❌ OCR no pudo extraer texto útil")
                return {}
        
        # Normalizar y procesar
        print("\n🔬 PASO 3: Normalizando texto...")
        normalized = self._normalize(text)
        
        print("\n🔬 PASO 4: Extrayendo datos...")
        return self._parse_text(normalized)
    
    def _clean_ocr_text(self, text: str) -> str:
        """Limpia texto OCR eliminando artefactos comunes - MEJORADO"""
        # Remover nombres de archivo comunes
        text = re.sub(r'\b\w+\.(jpg|jpeg|png|pdf|webp)\b', '', text, flags=re.IGNORECASE)
        # Remover patrones de fecha/hora de sistema
        text = re.sub(r'\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}', '', text)
        # Remover URLs
        text = re.sub(r'https?://[^\s]+', '', text)
        # Remover dimensiones de imagen como (1352×818)
        text = re.sub(r'\(\d+×\d+\)', '', text)
        # Remover "see-sol-factura-" y similares
        text = re.sub(r'see-sol-factura[^\s]*', '', text, flags=re.IGNORECASE)
        
        # Remover líneas muy cortas que son probablemente ruido
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line_clean = line.strip()
            # Mantener líneas que tengan contenido sustancial y no sean solo números/símbolos
            if (len(line_clean) > 5 and 
                not re.match(r'^\d+/\d+$', line_clean) and  # No "1/1"
                not re.match(r'^[_\-\|]+$', line_clean) and  # No líneas de símbolos
                not re.match(r'^\s*$', line_clean)):  # No líneas vacías
                cleaned_lines.append(line_clean)
        
        return '\n'.join(cleaned_lines)
    
    def _is_text_garbled(self, text: str) -> bool:
        """
        Detecta si el texto es basura - MEJORADO para detectar metadatos de imagen
        """
        text_stripped = text.strip()
        
        if not text_stripped:
            return True
            
        # Si contiene patrones típicos de metadatos de imagen/web
        metadata_patterns = [
            r'\.(jpg|jpeg|png|webp)',
            r'https?://',
            r'\d+x\d+',  # dimensiones
            r'\d+×\d+',  # dimensiones
            r'\d{1,2}/\d{1,2}/\d{2,4},\s*\d{1,2}:\d{2}',  # fecha/hora sistema
        ]
        
        for pattern in metadata_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Si el texto es razonablemente largo y tiene contenido de factura, no es basura
        if len(text_stripped) > 200:
            keywords = ['FACTURA', 'BOLETA', 'RUC', 'TOTAL', 'CLIENTE', 'MONTO']
            text_upper = text.upper()
            found_keywords = sum(1 for kw in keywords if kw in text_upper)
            if found_keywords >= 2:
                return False
        
        # Si es muy corto, probablemente es basura
        if len(text_stripped) < 50:
            return True
            
        return False
    
    def _has_invoice_keywords(self, text: str) -> bool:
        """
        Verifica si el texto contiene palabras clave de facturas - MEJORADO
        """
        keywords = [
            'FACTURA', 'ELECTRONICA', 'BOLETA', 'RUC', 
            'Fecha', 'Total', 'Importe', 'Cliente', 'Emisión',
            'Serie', 'Número', 'Monto', 'Señor', 'MONEDA',
            'IGV', 'SOLES', 'PEN', 'DIRECCION', 'CIUDAD',
            'NOTA', 'CREDITO', 'DEBITO', 'COMPROBANTE', 'PAGO',
            'EMISOR', 'RECEPTOR', 'DOCUMENTO', 'COMERCIAL'
        ]
        text_upper = text.upper()
        found = sum(1 for kw in keywords if kw.upper() in text_upper)
        
        print(f"🔍 Palabras clave encontradas: {found}/{len(keywords)}")
        return found >= 2
    
    def parse_image_with_ocr(self, image_path: str) -> Dict[str, Any]:
        """
        Extrae texto de una imagen usando OCR - MEJORADO
        """
        try:
            print("🔬 Procesando imagen con OCR...")
            text = _extract_text_with_ocr(image_path)
            
            if not text:
                print("❌ No se pudo extraer texto de la imagen")
                return {}
            
            print(f"✅ Texto extraído: {len(text)} caracteres")
            # Limpiar texto OCR
            text = self._clean_ocr_text(text)
            print("📝 Texto después de limpieza:")
            print("-" * 50)
            print(text[:800])
            print("-" * 50)
            
            normalized = self._normalize(text)
            return self._parse_text(normalized)
            
        except Exception as e:
            print(f"❌ Error en OCR: {e}")
            import traceback
            traceback.print_exc()
            return {}
    
    def _parse_text(self, normalized: str) -> Dict[str, Any]:
        """
        Extrae datos de factura del texto normalizado - MEJORADO
        """
        data: Dict[str, Any] = {}
        
        print("\n" + "="*60)
        print("🔍 INICIANDO EXTRACCIÓN DE DATOS")
        print("="*60)
        
        # 1. Número de factura - PATRONES MEJORADOS
        print("\n1️⃣ Buscando número de factura...")
        inv_num = self._extract_invoice_number(normalized)
        if inv_num:
            data["invoice_number"] = inv_num
            print(f"   ✅ Encontrado: {inv_num}")
        else:
            print("   ❌ No encontrado")
        
        # 2. Fecha de emisión - PATRONES MEJORADOS
        print("\n2️⃣ Buscando fecha de emisión...")
        inv_date = self._extract_invoice_date(normalized)
        if inv_date:
            data["invoice_date"] = self._normalize_date(inv_date)
            print(f"   ✅ Encontrado: {inv_date} → {data['invoice_date']}")
        else:
            print("   ❌ No encontrada")
        
        # 3. Fecha de vencimiento - MEJORADO
        print("\n3️⃣ Buscando fecha de vencimiento...")
        due_date = self._extract_due_date(normalized)
        if due_date:
            data["due_date"] = self._normalize_date(due_date)
            print(f"   ✅ Encontrado: {due_date}")
        else:
            print("   ❌ No encontrada")
        
        # 4. Monto - PATRONES MEJORADOS
        print("\n4️⃣ Buscando monto...")
        amount = self._extract_amount(normalized)
        if amount:
            data["amount"] = amount
            print(f"   ✅ Encontrado: S/ {amount}")
        else:
            print("   ❌ No encontrado")
        
        # 5. RUC - MEJORADO
        print("\n5️⃣ Buscando RUC del cliente...")
        ruc = self._extract_ruc(normalized)
        if ruc:
            data["ruc"] = ruc
            print(f"   ✅ Encontrado: {ruc}")
        else:
            print("   ❌ No encontrado")
        
        # 6. Nombre del cliente - MEJORADO
        print("\n6️⃣ Buscando nombre del cliente...")
        client_name = self._extract_client_name(normalized)
        if client_name:
            data["client_name"] = client_name
            print(f"   ✅ Encontrado: {client_name}")
        else:
            print("   ❌ No encontrado")
        
        # 7. Referencia bancaria - MEJORADO
        print("\n7️⃣ Buscando referencia bancaria...")
        bank_ref = self._extract_bank_reference(normalized)
        if bank_ref:
            data["bank_reference"] = bank_ref
            print(f"   ✅ Encontrado: {bank_ref}")
        else:
            print("   ❌ No encontrado")
        
        print("\n" + "="*60)
        print(f"📊 RESUMEN: {len(data)} campos extraídos")
        print("="*60)
        
        return data
    
    def _extract_invoice_number(self, text: str) -> Optional[str]:
        """Extrae número de factura - PATRONES MEJORADOS"""
        patterns = [
            r"\b([A-Z]{2}\d{2}[-]\d{8,13})\b",  # Boleta: EB01-3710717040134
            r"\b([A-Z]\d{3}[-]\d{1,8})\b",      # Factura: E001-1211, F001-123
            r"\b([A-Z]{1,2}\d{3,4}[-]\d{1,8})\b", # Más flexible
            r"\b([A-Z]\d{3}\s*\d{1,8})\b",      # E001 4211 (sin guión)
            r"Nro\.?\s*:?\s*([A-Z0-9-\s]+)",    # Nro. F001-00000384 o E001 4211
            r"Numero\.?\s*:?\s*([A-Z0-9-\s]+)", # Numero F001-00000384
            r"FACTURA\s+ELECTRONICA\s+([A-Z0-9-\s]+)", # FACTURA ELECTRONICA F001-00000384
            r"BOLETA\s+ELECTRONICA\s+([A-Z0-9-\s]+)",  # BOLETA ELECTRONICA EB01-123
            r"COMPROBANTE\s+([A-Z0-9-\s]+)",           # COMPROBANTE F001-123
            r"\bE001\s*4211\b",                       # Específico para este caso
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            if matches:
                print(f"   🔍 Patrón '{pattern}' encontró: {matches}")
                # Buscar el que parece más válido
                for match in matches:
                    cleaned_match = re.sub(r'\s+', '-', match.strip())  # Reemplazar espacios con guiones
                    if len(cleaned_match) >= 6:  # Mínimo F001-1
                        return cleaned_match
        return None
    
    def _extract_invoice_date(self, text: str) -> Optional[str]:
        """Extrae fecha de emisión - MEJORADO con más patrones"""
        # Buscar patrones de fecha en cualquier lugar - MÁS PATRONES
        date_patterns = [
            r"(\d{1,2}[-/]\d{1,2}[-/]\d{2,4})",  # dd/mm/yyyy o dd-mm-yyyy
            r"(\d{1,2}[-/]\w{3,9}[-/]\d{4})",    # dd-mmm-yyyy
            r"(\d{4}[-/]\d{1,2}[-/]\d{1,2})",    # yyyy-mm-dd
            r"(\d{1,2}\s+de\s+\w+\s+de\s+\d{4})", # 25 de noviembre de 2025
            r"(\d{1,2}\s+\w+\s+\d{4})",           # 25 noviembre 2025
            r"(\d{1,2}[/-]\d{1,2}[/-]\d{2})",     # dd/mm/yy
            r"Fecha\s*:\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})", # Fecha: 25/11/2025
        ]
        
        # Buscar cerca de palabras clave de fecha - MÁS PALABRAS CLAVE
        keywords = [
            "Emisión", "Emision", "Fecha", "Date", "Emitido", "Emisor",
            "FECHA", "FECHA DE EMISIÓN", "FECHA EMISIÓN", "EMITIDO",
            "Fecha de Emisión", "Fecha Emisión"
        ]
        
        for keyword in keywords:
            # Buscar la palabra clave (case insensitive)
            matches = list(re.finditer(re.escape(keyword), text, re.IGNORECASE))
            for match in matches:
                # Buscar en el contexto alrededor de la palabra clave
                start = max(0, match.start() - 50)
                end = min(len(text), match.end() + 100)
                context = text[start:end]
                
                print(f"   🔍 Buscando fecha cerca de '{keyword}': {context[:50]}...")
                
                for pattern in date_patterns:
                    date_match = re.search(pattern, context, re.IGNORECASE)
                    if date_match:
                        date_found = date_match.group(1)
                        print(f"   ✅ Fecha encontrada con patrón '{pattern}': {date_found}")
                        return date_found
        
        # Buscar cualquier fecha en el texto que parezca reciente
        all_dates = []
        for pattern in date_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for date_str in matches:
                # Verificar que sea una fecha válida
                if self._is_valid_date(date_str):
                    all_dates.append(date_str)
        
        if all_dates:
            print(f"   🔍 Fechas encontradas en texto: {all_dates}")
            # Preferir fechas que parezcan recientes
            for date_str in all_dates:
                if any(year in date_str for year in ['2025', '2024', '2023', '2026']):
                    return date_str
                if re.search(r'20[2-3][0-9]', date_str):  # 2020-2039
                    return date_str
            return all_dates[0]  # Devolver la primera encontrada
        
        # Si no se encuentra fecha, buscar números que parezcan fechas
        print("   🔍 Buscando patrones de fecha alternativos...")
        alternative_patterns = [
            r"\b(\d{1,2})[/-](\d{1,2})[/-](\d{2,4})\b",
            r"\b(\d{1,2})\s+(\d{1,2})\s+(\d{2,4})\b",
        ]
        
        for pattern in alternative_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                d, m, y = match
                # Verificar si parece una fecha válida
                if 1 <= int(d) <= 31 and 1 <= int(m) <= 12:
                    date_str = f"{d}/{m}/{y}"
                    print(f"   ✅ Fecha alternativa encontrada: {date_str}")
                    return date_str
        
        print("   ❌ No se encontraron fechas en el texto")
        return None
    
    def _extract_due_date(self, text: str) -> Optional[str]:
        """Extrae fecha de vencimiento - MEJORADO"""
        # Buscar específicamente "Fecha de Vencimiento"
        vencimiento_patterns = [
            r"Fecha\s*de\s*Vencimiento\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"Vencimiento\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"Vence\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
            r"Fecha\s*Vencimiento\s*[:\-]?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
        ]
        
        for pattern in vencimiento_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1)
        
        # Buscar cerca de "Fecha de Vencimiento" aunque no tenga fecha explícita
        vencimiento_match = re.search(r"Fecha\s*de\s*Vencimiento", text, re.IGNORECASE)
        if vencimiento_match:
            # Buscar cualquier fecha después de "Fecha de Vencimiento"
            context = text[vencimiento_match.end():vencimiento_match.end() + 50]
            date_patterns = [
                r"(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})",
                r"(\d{1,2}[-/]\w{3,9}[-/]\d{4})",
            ]
            for pattern in date_patterns:
                date_match = re.search(pattern, context)
                if date_match:
                    return date_match.group(1)
        
        return None
    
    def _is_valid_date(self, date_str: str) -> bool:
        """Verifica si una cadena parece ser una fecha válida"""
        try:
            # Patrones comunes de fecha
            patterns = [
                r'\d{1,2}[/-]\d{1,2}[/-]\d{2,4}',
                r'\d{1,2}[-/]\w{3,9}[-/]\d{4}',
                r'\d{4}[-/]\d{1,2}[-/]\d{1,2}',
                r'\d{1,2}\s+de\s+\w+\s+de\s+\d{4}',
            ]
            
            for pattern in patterns:
                if re.match(pattern, date_str, re.IGNORECASE):
                    return True
            return False
        except:
            return False
    
    def _extract_amount(self, text: str) -> Optional[Decimal]:
        """Extrae monto total - MEJORADO"""
        patterns = [
            r"Importe\s*Total\s*[:\-]?\s*S?/?\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:[.,][0-9]{2})?)",
            r"TOTAL\s*[:\-]?\s*S?/?\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:[.,][0-9]{2})?)",
            r"MONTO\s*TOTAL\s*[:\-]?\s*S?/?\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:[.,][0-9]{2})?)",
            r"Valor\s*Unitario\s*[:\-]?\s*S?/?\s*([0-9]{1,3}(?:\.[0-9]{3})*(?:[.,][0-9]{2})?)",
            r"\bS?/?\s*([0-9]{1,3}(?:\.[0-9]{3})*[.,][0-9]{2})\b",
            r"\b([0-9]{1,3}(?:\.[0-9]{3})*[.,][0-9]{2})\s*S?/?\s*",
        ]
        
        # Buscar montos que parezcan importes de factura (no 1.00, 0.00, etc.)
        candidate_amounts = []
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for amount_str in matches:
                try:
                    # Normalizar formato
                    if '.' in amount_str and ',' in amount_str:
                        amount_clean = amount_str.replace('.', '').replace(',', '.')
                    elif ',' in amount_str:
                        amount_clean = amount_str.replace(',', '.')
                    else:
                        amount_clean = amount_str
                    
                    amount_decimal = Decimal(amount_clean)
                    # Filtrar montos que sean razonables para una factura
                    if 10.00 <= amount_decimal <= 1000000:  # Entre S/ 10 y 1 millón
                        candidate_amounts.append((amount_decimal, amount_str))
                except:
                    continue
        
        if candidate_amounts:
            # Ordenar por monto y tomar el más alto (probablemente el total)
            candidate_amounts.sort(reverse=True)
            print(f"   🔍 Montos candidatos: {candidate_amounts}")
            return candidate_amounts[0][0]
        
        return None
    
    def _extract_ruc(self, text: str) -> Optional[str]:
        """Extrae RUC del cliente - MEJORADO"""
        # Buscar RUC en cualquier lugar del texto
        ruc_pattern = r"\b(\d{11})\b"
        matches = re.findall(ruc_pattern, text)
        
        if matches:
            # Filtrar RUCs que parezcan válidos (no todos ceros, etc.)
            for ruc in matches:
                if not re.match(r'^0+$', ruc):  # No todos ceros
                    if ruc.startswith('10') or ruc.startswith('20'):  # RUCs peruanos típicos
                        return ruc
            return matches[0]  # Devolver el primero si no se encontró uno "ideal"
        
        return None
    
    def _extract_client_name(self, text: str) -> Optional[str]:
        """Extrae nombre del cliente - MEJORADO"""
        # Método 1: Buscar después de "Cliente:"
        match = re.search(r"Cliente\s*[:\-]?\s*([^\n]+)", text, re.IGNORECASE)
        if match:
            nombre = match.group(1).strip()
            # Limpiar el nombre (remover RUC, etc.)
            nombre = re.sub(r'\s*RUC\s*\d.*$', '', nombre, flags=re.IGNORECASE)
            nombre = re.sub(r'\s+', ' ', nombre).strip()
            if len(nombre) > 3:
                return nombre
        
        # Método 2: Buscar después de "Señor(es)"
        match = re.search(r"Señor\(es\)\s*[:\-]?\s*([^\n]+)", text, re.IGNORECASE)
        if match:
            nombre = match.group(1).strip()
            nombre = re.sub(r'\s*RUC\s*\d.*$', '', nombre, flags=re.IGNORECASE)
            nombre = re.sub(r'\s+', ' ', nombre).strip()
            if len(nombre) > 3:
                return nombre
        
        # Método 3: Buscar patrones de empresa
        empresa_patterns = [
            r"([A-Z&][A-Z\s&]+(?:S\.A\.|S\.A\.C\.|E\.I\.R\.L\.|S\.R\.L\.|S\.A\.S\.))",
            r"([A-Z][a-zA-Z\s&]+(?:S\.A\.|S\.A\.C\.|E\.I\.R\.L\.|S\.R\.L\.))",
        ]
        
        for pattern in empresa_patterns:
            match = re.search(pattern, text)
            if match:
                nombre = match.group(1).strip()
                if len(nombre) > 5:
                    return nombre
        
        return None
    
    def _extract_bank_reference(self, text: str) -> Optional[str]:
        """Extrae referencia bancaria - MEJORADO para evitar falsos positivos"""
        patterns = [
            r"Referencia\s*bancaria\s*[:\-]?\s*([A-Z0-9\-]{4,})",
            r"Código\s*de\s*operaci[oó]n\s*[:\-]?\s*([A-Z0-9\-]{4,})",
            r"\b(BR[-_]?[0-9A-Z]{4,})\b",
            r"Operaci[oó]n\s*[:\-]?\s*([A-Z0-9\-]{4,})",
            r"Ref\.?\s*[:\-]?\s*([A-Z0-9\-]{4,})",
        ]
        
        result = self._match_first(text, patterns)
        # Filtrar resultados muy cortos que probablemente sean falsos positivos
        if result and len(result) >= 4:
            return result
        return None
    
    def parse(self, file_path: str) -> Dict[str, Any]:
        """Método de compatibilidad"""
        return self.parse_pdf_smart(file_path)
    
    def _extract_text_improved(self, file_path: str) -> Optional[str]:
        return _extract_text_improved(file_path)
    
    def _normalize(self, text: str) -> str:
        return _normalize(text)
    
    def _match_first(self, text: str, patterns: List[str]) -> Optional[str]:
        return _match_first(text, patterns)
    
    def _normalize_date(self, raw: str) -> str:
        return _normalize_date(raw)


# ============================================================================
# FUNCIONES AUXILIARES
# ============================================================================

def _extract_text_improved(file_path: str) -> Optional[str]:
    """Extrae texto de PDF con múltiples métodos"""
    try:
        import pdfplumber
        
        with pdfplumber.open(file_path) as pdf:
            all_text = []
            
            for i, page in enumerate(pdf.pages):
                print(f"   📄 Procesando página {i+1}...")
                
                # Método 1: Extracción normal
                text = page.extract_text()
                
                if not text or len(text.strip()) < 20:
                    # Método 2: Con layout
                    text = page.extract_text(layout=True)
                
                if not text or len(text.strip()) < 20:
                    # Método 3: Tablas
                    tables = page.extract_tables()
                    if tables:
                        table_text = []
                        for table in tables:
                            for row in table:
                                if row:
                                    table_text.append(" ".join([str(c) if c else "" for c in row]))
                        text = "\n".join(table_text)
                
                if text and len(text.strip()) >= 20:
                    all_text.append(text)
                    print(f"      ✓ Extraídos {len(text)} caracteres")
                else:
                    print(f"      ⚠️ Texto insuficiente")
            
            if all_text:
                result = "\n".join(all_text)
                print(f"   ✅ Total: {len(result)} caracteres de {len(all_text)} página(s)")
                return result
            else:
                print(f"   ❌ No se extrajo texto útil")
                return None
                
    except ImportError:
        print("   ❌ pdfplumber no instalado")
        return None
    except Exception as e:
        print(f"   ❌ Error: {e}")
        return None


def _normalize(text: str) -> str:
    """Normaliza espacios preservando saltos de línea"""
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _match_first(text: str, patterns: List[str]) -> Optional[str]:
    """Busca el primer patrón que coincida"""
    for pat in patterns:
        try:
            m = re.search(pat, text, flags=re.IGNORECASE)
            if m:
                if m.lastindex and m.lastindex >= 1:
                    return m.group(1).strip()
                else:
                    return m.group(0).strip()
        except Exception:
            continue
    return None


def _normalize_date(raw: str) -> str:
    """Convierte fechas a formato yyyy-mm-dd"""
    raw = raw.strip()
    
    meses_es = {
        'ene': '01', 'enero': '01', 'feb': '02', 'febrero': '02',
        'mar': '03', 'marzo': '03', 'abr': '04', 'abril': '04',
        'may': '05', 'mayo': '05', 'jun': '06', 'junio': '06',
        'jul': '07', 'julio': '07', 'ago': '08', 'agosto': '08',
        'sep': '09', 'sept': '09', 'septiembre': '09',
        'oct': '10', 'octubre': '10', 'nov': '11', 'noviembre': '11',
        'dic': '12', 'diciembre': '12',
    }
    
    # Con mes en texto: 23-abr-2025
    m = re.match(r"(\d{1,2})[-/](\w{3,9})[-/](\d{4})", raw, re.IGNORECASE)
    if m:
        d, mes_texto, y = m.groups()
        if mes_texto.lower() in meses_es:
            return f"{y}-{meses_es[mes_texto.lower()]}-{d.zfill(2)}"
    
    # Numérico: dd/mm/yyyy o dd-mm-yyyy
    m = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{4})", raw)
    if m:
        d, mth, y = m.groups()
        return f"{y}-{mth.zfill(2)}-{d.zfill(2)}"
    
    # Numérico: dd/mm/yy (años cortos)
    m = re.match(r"(\d{1,2})[/-](\d{1,2})[/-](\d{2})", raw)
    if m:
        d, mth, y = m.groups()
        year = f"20{y}" if int(y) < 50 else f"19{y}"  # Asumir siglo
        return f"{year}-{mth.zfill(2)}-{d.zfill(2)}"
    
    # Ya en formato correcto
    if re.match(r"\d{4}-\d{2}-\d{2}", raw):
        return raw
    
    return raw


def _extract_text_with_ocr(image_path: str) -> Optional[str]:
    """Extrae texto de imagen con OCR"""
    try:
        import pytesseract
        from PIL import Image
        
        image = Image.open(image_path)
        custom_config = r'--oem 3 --psm 6 -l spa+eng'
        text = pytesseract.image_to_string(image, config=custom_config)
        
        return text if text.strip() else None
        
    except ImportError:
        print("❌ pytesseract o Pillow no instalados")
        return None
    except Exception as e:
        print(f"❌ Error en OCR: {e}")
        return None


def _extract_text_from_pdf_with_ocr(pdf_path: str) -> Optional[str]:
    """Convierte PDF a imagen y usa OCR - MEJORADO para mayor robustez"""
    try:
        from pdf2image import convert_from_path
        import pytesseract
        
        print("   🔄 Convirtiendo PDF a imagen con Poppler...")
        
        # Usar poppler_path si está disponible
        poppler_kwargs = {}
        if POPPLER_PATH:
            print(f"   📁 Usando Poppler desde: {POPPLER_PATH}")
            poppler_kwargs['poppler_path'] = POPPLER_PATH
        
        try:
            # Convertir más páginas por si acaso
            images = convert_from_path(pdf_path, first_page=1, last_page=2, **poppler_kwargs)
        except Exception as e:
            print(f"   ⚠️ Error con Poppler: {e}")
            print("   🔄 Intentando sin Poppler...")
            images = convert_from_path(pdf_path, first_page=1, last_page=2)
        
        if not images:
            print("   ❌ No se pudieron generar imágenes del PDF")
            return None
        
        print(f"   ✅ PDF convertido a {len(images)} imagen(es)")
        print("   🔍 Aplicando OCR con Tesseract...")
        
        # Configurar Tesseract si está disponible
        try:
            if TESSERACT_PATH and not pytesseract.pytesseract.tesseract_cmd:
                pytesseract.pytesseract.tesseract_cmd = TESSERACT_PATH
        except:
            pass
        
        all_text = []
        for i, image in enumerate(images):
            print(f"   📄 Procesando imagen {i+1}...")
            custom_config = r'--oem 3 --psm 6 -l spa+eng'
            text = pytesseract.image_to_string(image, config=custom_config)
            if text and text.strip():
                all_text.append(text)
        
        if all_text:
            combined_text = '\n'.join(all_text)
            print(f"   ✅ OCR exitoso: {len(combined_text)} caracteres extraídos")
            return combined_text
        else:
            print("   ⚠️ OCR no extrajo texto")
            return None
        
    except ImportError as e:
        print(f"   ❌ Librería faltante: {e}")
        return None
    except Exception as e:
        print(f"   ❌ Error en OCR de PDF: {e}")
        return None