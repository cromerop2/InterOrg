/** Componentes accesibles compartidos por las pantallas de Android, iOS y web. */
import React, { useState } from 'react';
import { Modal, Pressable, ScrollView, StyleSheet, Text, TextInput, View } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
export const colors = { navy:'#142e51', green:'#078d68', muted:'#708098', line:'#e1e8ef', background:'#f3f6fa' };
export const s = StyleSheet.create({
  screen:{flex:1,backgroundColor:colors.background},content:{padding:20,paddingBottom:36,gap:16},
  header:{paddingHorizontal:22,paddingVertical:16,backgroundColor:'#fff',borderBottomWidth:1,borderBottomColor:colors.line,flexDirection:'row',alignItems:'center',justifyContent:'space-between'},
  brand:{fontSize:17,fontWeight:'800',letterSpacing:1,color:colors.navy},subtitle:{fontSize:11,color:colors.muted,marginTop:3},
  title:{fontSize:23,fontWeight:'800',color:colors.navy,letterSpacing:-.5},h2:{fontSize:17,fontWeight:'700',color:colors.navy},
  text:{fontSize:13,color:colors.muted,lineHeight:21},label:{fontSize:12,fontWeight:'600',color:colors.muted,marginBottom:8},
  card:{padding:20,backgroundColor:'#fff',borderWidth:1,borderColor:colors.line,borderRadius:12,gap:13},
  input:{backgroundColor:'#fff',borderWidth:1,borderColor:'#d6e0eb',paddingHorizontal:13,paddingVertical:13,borderRadius:8,fontSize:15,color:colors.navy,minHeight:48},
  button:{backgroundColor:colors.green,borderRadius:8,padding:14,minHeight:48,alignItems:'center',justifyContent:'center'},
  buttonText:{color:'#fff',fontWeight:'700',fontSize:13},secondary:{backgroundColor:'#eaf0f5'},secondaryText:{color:colors.navy},
  error:{color:'#a52c3b',fontSize:13,lineHeight:20},notice:{padding:15,backgroundColor:'#e5f5ed',borderRadius:9},
  row:{flexDirection:'row',alignItems:'center',gap:12},between:{flexDirection:'row',justifyContent:'space-between',alignItems:'center',gap:10},
  badge:{backgroundColor:'#e8f6ef',color:'#13765b',fontSize:10,fontWeight:'700',paddingHorizontal:9,paddingVertical:5,borderRadius:5,overflow:'hidden'},
  tabs:{flexDirection:'row',backgroundColor:'#fff',borderTopWidth:1,borderTopColor:colors.line,paddingVertical:10,paddingHorizontal:8},
  tab:{flex:1,paddingVertical:6,alignItems:'center',gap:4,minHeight:48},tabText:{fontSize:10,color:colors.muted,fontWeight:'600'},tabActive:{color:colors.green},
  hero:{backgroundColor:colors.navy,borderRadius:14,padding:24,gap:12},heroTitle:{fontSize:29,fontWeight:'800',color:'#fff',letterSpacing:-.8},eyebrow:{fontSize:9,fontWeight:'700',letterSpacing:2,color:'#a7daca'},
  stat:{flex:1,padding:15,backgroundColor:'#fff',borderWidth:1,borderColor:colors.line,borderRadius:10,gap:7},statNumber:{fontSize:25,fontWeight:'800',color:colors.navy},statLabel:{fontSize:9,color:colors.muted},
  score:{fontSize:24,fontWeight:'800',color:colors.navy,textAlign:'center'},team:{flex:1,fontSize:14,fontWeight:'700',color:colors.navy,textAlign:'center'},
  listItem:{paddingVertical:14,borderBottomWidth:1,borderBottomColor:colors.line},selection:{padding:14,borderRadius:7,backgroundColor:'#eaf7f0'},
});
export function Button({title,onPress,secondary=false,disabled=false}:{title:string;onPress:()=>void;secondary?:boolean;disabled?:boolean}) {
  return <Pressable accessibilityRole="button" accessibilityLabel={title} accessibilityState={{disabled}} disabled={disabled} onPress={onPress} style={[s.button,secondary&&s.secondary,disabled&&{opacity:.45}]}><Text style={[s.buttonText,secondary&&s.secondaryText]}>{title}</Text></Pressable>;
}
export function Field({label,value,onChange,secure=false,numeric=false,placeholder='',autoCapitalize='sentences'}:{label:string;value:string;onChange:(v:string)=>void;secure?:boolean;numeric?:boolean;placeholder?:string;autoCapitalize?:'none'|'sentences'}) {
  return <View><Text style={s.label}>{label}</Text><TextInput accessibilityLabel={label} style={s.input} value={value} onChangeText={onChange} secureTextEntry={secure} keyboardType={numeric?'number-pad':'default'} autoCapitalize={secure?'none':autoCapitalize} autoCorrect={!secure && autoCapitalize!=='none'} placeholder={placeholder} placeholderTextColor="#a0adbb"/></View>;
}
export type Option = {id:string;label:string};
export function Choice({label,value,options,onChange}:{label:string;value:string;options:Option[];onChange:(v:string)=>void}) {
  const [visible,setVisible] = useState(false);
  const [search,setSearch] = useState('');
  return <View><Text style={s.label}>{label}</Text><Pressable accessibilityRole="button" accessibilityLabel={label} onPress={()=>{setSearch('');setVisible(true);}} style={[s.input,s.between]}><Text style={{color:colors.navy,flex:1}}>{options.find(o=>o.id===value)?.label || 'Selecciona…'}</Text><Text>⌄</Text></Pressable>
    <Modal visible={visible} animationType="slide" onRequestClose={()=>setVisible(false)}><SafeAreaView style={s.screen}><View style={s.content}><View style={s.between}><Text style={s.h2}>{label}</Text><Button title="Cerrar" secondary onPress={()=>setVisible(false)}/></View><TextInput accessibilityLabel="Buscar opción" placeholder="Buscar…" style={s.input} value={search} onChangeText={setSearch}/></View><ScrollView contentContainerStyle={{paddingHorizontal:20,paddingBottom:30}}>{options.filter(o=>o.label.toLocaleLowerCase().includes(search.toLocaleLowerCase())).map(o=><Pressable accessibilityRole="button" key={o.id} onPress={()=>{onChange(o.id);setVisible(false);}} style={[s.listItem,value===o.id&&s.selection]}><Text style={s.h2}>{o.label}</Text></Pressable>)}{!options.length&&<Text style={s.text}>Aún no hay opciones disponibles.</Text>}</ScrollView></SafeAreaView></Modal></View>;
}
